from abc import abstractmethod
from typing import Collection, Tuple, List, Union

import mongomock
import pymongo.collection
from fastapi import HTTPException

from optimade.filterparser import LarkParser
from optimade.filtertransformers.mongo import NewMongoTransformer
from optimade.models import NonnegativeInt, EntryResource

from .config import CONFIG
from .deps import EntryListingQueryParams, SingleEntryQueryParams
from .mappers import ResourceMapper


if CONFIG.use_real_mongo:
    from pymongo import MongoClient
else:
    from mongomock import MongoClient

client = MongoClient()


class EntryCollection(Collection):  # pylint: disable=inherit-non-class
    def __init__(
        self, collection, resource_cls: EntryResource, resource_mapper: ResourceMapper
    ):
        self.collection = collection
        self.parser = LarkParser()
        self.resource_cls = resource_cls
        self.resource_mapper = resource_mapper

    def __len__(self):
        return self.collection.count()

    def __iter__(self):
        return self.collection.find()

    def __contains__(self, entry):
        return self.collection.count(entry) > 0

    def get_attribute_fields(self) -> set:
        schema = self.resource_cls.schema()
        attributes = schema["properties"]["attributes"]
        if "allOf" in attributes:
            allOf = attributes.pop("allOf")
            for dict_ in allOf:
                attributes.update(dict_)
        if "$ref" in attributes:
            path = attributes["$ref"].split("/")[1:]
            attributes = schema.copy()
            while path:
                next_key = path.pop(0)
                attributes = attributes[next_key]
        return set(attributes["properties"].keys())

    @abstractmethod
    def find(
        self, params: EntryListingQueryParams
    ) -> Tuple[List[EntryResource], NonnegativeInt, bool, set]:
        """
        Fetches results and indicates if more data is available.

        Also gives the total number of data available in the absence of page_limit.

        Args:
            params (EntryListingQueryParams): entry listing URL query params

        Returns:
            Tuple[List[Entry], NonnegativeInt, bool, set]: (results, data_returned, more_data_available, fields)

        """

    def count(self, **kwargs):
        return self.collection.count(**kwargs)


class MongoCollection(EntryCollection):
    def __init__(
        self,
        collection: Union[
            pymongo.collection.Collection, mongomock.collection.Collection
        ],
        resource_cls: EntryResource,
        resource_mapper: ResourceMapper,
    ):
        super().__init__(collection, resource_cls, resource_mapper)
        self.transformer = NewMongoTransformer()

        self.provider = CONFIG.provider["prefix"]
        self.provider_fields = CONFIG.provider_fields.get(resource_mapper.ENDPOINT, [])
        self.page_limit = CONFIG.page_limit
        self.parser = LarkParser(
            version=(0, 10, 0), variant="default"
        )  # The NewMongoTransformer only supports v0.10.0 as the latest grammar

    def __len__(self):
        return self.collection.estimated_document_count()

    def __contains__(self, entry):
        return self.collection.count_documents(entry.dict()) > 0

    def count(self, **kwargs):
        for k in list(kwargs.keys()):
            if k not in ("filter", "skip", "limit", "hint", "maxTimeMS"):
                del kwargs[k]
        if "filter" not in kwargs:  # "filter" is needed for count_documents()
            kwargs["filter"] = {}
        return self.collection.count_documents(**kwargs)

    def find(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> Tuple[List[EntryResource], NonnegativeInt, bool, set]:
        criteria = self._parse_params(params)

        all_fields = criteria.pop("fields")
        if getattr(params, "response_fields", False):
            fields = set(params.response_fields.split(","))
        else:
            fields = all_fields.copy()

        results = []
        for doc in self.collection.find(**criteria):
            results.append(self.resource_cls(**self.resource_mapper.map_back(doc)))

        if isinstance(params, EntryListingQueryParams):
            nresults_now = len(results)
            criteria_nolimit = criteria.copy()
            criteria_nolimit.pop("limit", None)
            data_returned = self.count(**criteria_nolimit)
            more_data_available = nresults_now < data_returned
        else:
            # SingleEntryQueryParams, e.g., /structures/{entry_id}
            data_returned = 1
            more_data_available = False
            if len(results) > 1:
                raise HTTPException(
                    status_code=404,
                    detail=f"Instead of a single entry, {len(results)} entries were found",
                )
            results = results[0] if results else None

        return results, data_returned, more_data_available, all_fields - fields

    def _alias_filter(self, filter_: dict) -> dict:
        res = {}
        for key, value in filter_.items():
            if key in ["$and", "$or"]:
                res[key] = [self._alias_filter(item) for item in value]
            else:
                new_value = value
                if isinstance(value, dict):
                    new_value = self._alias_filter(value)
                res[self.resource_mapper.alias_for(key)] = new_value
        return res

    def _parse_params(
        self, params: Union[EntryListingQueryParams, SingleEntryQueryParams]
    ) -> dict:
        cursor_kwargs = {}

        if getattr(params, "filter", False):
            tree = self.parser.parse(params.filter)
            mongo_filter = self.transformer.transform(tree)
            cursor_kwargs["filter"] = self._alias_filter(mongo_filter)
        else:
            cursor_kwargs["filter"] = {}

        if (
            getattr(params, "response_format", False)
            and params.response_format != "json"
        ):
            raise HTTPException(
                status_code=400, detail="Only 'json' response_format supported"
            )

        if getattr(params, "page_limit", False):
            limit = self.page_limit
            if params.page_limit != self.page_limit:
                limit = params.page_limit
            if limit > self.page_limit:
                raise HTTPException(
                    status_code=400, detail=f"Max page_limit is {self.page_limit}"
                )
            if limit == 0:
                limit = self.page_limit
            cursor_kwargs["limit"] = limit

        # All OPTiMaDe fields
        fields = {"id", "type"}
        fields |= self.get_attribute_fields()
        # All provider-specific fields
        fields |= {self.provider + _ for _ in self.provider_fields}
        cursor_kwargs["fields"] = fields
        cursor_kwargs["projection"] = [
            self.resource_mapper.alias_for(f) for f in fields
        ]

        if getattr(params, "sort", False):
            sort_spec = []
            for elt in params.sort.split(","):
                field = elt
                sort_dir = 1
                if elt.startswith("-"):
                    field = field[1:]
                    sort_dir = -1
                sort_spec.append((field, sort_dir))
            cursor_kwargs["sort"] = sort_spec

        if getattr(params, "page_offset", False):
            cursor_kwargs["skip"] = params.page_offset

        return cursor_kwargs
