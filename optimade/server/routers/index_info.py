from typing import Union

from fastapi import APIRouter
from starlette.requests import Request

from optimade.models import (
    ErrorResponse,
    IndexInfoResponse,
    IndexInfoAttributes,
    IndexInfoResource,
    IndexRelationship,
)

from optimade.server.config import CONFIG

from .utils import meta_values


router = APIRouter()


@router.get(
    "/info",
    response_model=Union[IndexInfoResponse, ErrorResponse],
    response_model_skip_defaults=False,
    tags=["Info"],
)
def get_info(request: Request):
    return IndexInfoResponse(
        meta=meta_values(str(request.url), 1, 1, more_data_available=False),
        data=IndexInfoResource(
            attributes=IndexInfoAttributes(
                api_version="v0.10",
                available_api_versions=[
                    {
                        "url": "http://localhost:5001/index/optimade/v0.10.0/",
                        "version": "0.10.0",
                    }
                ],
                entry_types_by_format={"json": ["links"]},
                available_endpoints=["info", "links"],
                is_index=True,
            ),
            relationships={
                "default": IndexRelationship(
                    data={"type": "child", "id": CONFIG.default_db}
                )
            },
        ),
    )
