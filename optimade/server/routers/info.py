from typing import Union

from fastapi import APIRouter
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from optimade.models import (
    ErrorResponse,
    InfoResponse,
    EntryInfoResponse,
    ReferenceResource,
    StructureResource,
)

from optimade.server.config import CONFIG

from .utils import meta_values, retrieve_queryable_properties


router = APIRouter()

ENTRY_INFO_SCHEMAS = {
    "structures": StructureResource.schema,
    "references": ReferenceResource.schema,
}


@router.get(
    "/info",
    response_model=Union[InfoResponse, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Info"],
)
def get_info(request: Request):
    from optimade.models import BaseInfoResource, BaseInfoAttributes

    return InfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=BaseInfoResource(
            id=BaseInfoResource.schema()["properties"]["id"]["const"],
            type=BaseInfoResource.schema()["properties"]["type"]["const"],
            attributes=BaseInfoAttributes(
                api_version=f"v{CONFIG.version}",
                available_api_versions=[
                    {
                        "url": f"http://localhost:5000/optimade/v{CONFIG.version}/",
                        "version": CONFIG.version,
                    }
                ],
                formats=["json"],
                available_endpoints=["info", "links"] + list(ENTRY_INFO_SCHEMAS.keys()),
                entry_types_by_format={"json": list(ENTRY_INFO_SCHEMAS.keys())},
                is_index=False,
            ),
        ),
    )


@router.get(
    "/info/{entry}",
    response_model=Union[EntryInfoResponse, ErrorResponse],
    response_model_exclude_unset=True,
    tags=["Info", "Structure", "Reference"],
)
def get_entry_info(request: Request, entry: str):
    from optimade.models import EntryInfoResource

    valid_entry_info_endpoints = ENTRY_INFO_SCHEMAS.keys()
    if entry not in valid_entry_info_endpoints:
        raise StarletteHTTPException(
            status_code=404,
            detail=f"Entry info not found for {entry}, valid entry info endpoints are: {valid_entry_info_endpoints}",
        )

    schema = ENTRY_INFO_SCHEMAS[entry]()
    queryable_properties = {"id", "type", "attributes"}
    properties = retrieve_queryable_properties(schema, queryable_properties)

    output_fields_by_format = {"json": list(properties.keys())}

    return EntryInfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=EntryInfoResource(
            formats=list(output_fields_by_format.keys()),
            description=schema.get("description", "Entry Resources"),
            properties=properties,
            output_fields_by_format=output_fields_by_format,
        ),
    )
