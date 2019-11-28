from typing import Union

from fastapi import APIRouter, Depends
from starlette.requests import Request

from optimade.models import (
    ErrorResponse,
    StructureResource,
    StructureResponseMany,
    StructureResponseOne,
)
from optimade.server.config import CONFIG
from optimade.server.deps import EntryListingQueryParams, SingleEntryQueryParams
from optimade.server.entry_collections import MongoCollection, client
from optimade.server.mappers import StructureMapper

from .utils import get_entries, get_single_entry

router = APIRouter()

structures_coll = MongoCollection(
    client[CONFIG.mongo_database]["structures"], StructureResource, StructureMapper
)


@router.get(
    "/structures",
    response_model=Union[StructureResponseMany, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_structures(request: Request, params: EntryListingQueryParams = Depends()):
    return get_entries(
        collection=structures_coll,
        response=StructureResponseMany,
        request=request,
        params=params,
    )


@router.get(
    "/structures/{entry_id:path}",
    response_model=Union[StructureResponseOne, ErrorResponse],
    response_model_skip_defaults=True,
    tags=["Structure"],
)
def get_single_structure(
    request: Request, entry_id: str, params: SingleEntryQueryParams = Depends()
):
    return get_single_entry(
        collection=structures_coll,
        entry_id=entry_id,
        response=StructureResponseOne,
        request=request,
        params=params,
    )
