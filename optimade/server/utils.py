import traceback

from typing import Dict, Any

from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from starlette.responses import JSONResponse

from optimade.models import Error, ErrorResponse
from optimade.server.routers.utils import meta_values

from .config import CONFIG


def general_exception(
    request: Request, exc: Exception, **kwargs: Dict[str, Any]
) -> JSONResponse:
    tb = "".join(
        traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
    )
    print(tb)

    try:
        status_code = exc.status_code
    except AttributeError:
        status_code = kwargs.get("status_code", 500)

    detail = getattr(exc, "detail", str(exc))

    errors = kwargs.get("errors", None)
    if not errors:
        errors = [
            Error(detail=detail, status=status_code, title=str(exc.__class__.__name__))
        ]

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            ErrorResponse(
                meta=meta_values(
                    url=str(request.url),
                    data_returned=0,
                    data_available=0,
                    more_data_available=False,
                    **{CONFIG.provider["prefix"] + "traceback": tb},
                ),
                errors=errors,
            ),
            skip_defaults=True,
        ),
    )


def get_providers():
    """Retrieve providers.json from /Materials-Consortia/OPTiMaDe"""
    import requests
    from bson.objectid import ObjectId

    mat_consortia_providers = requests.get(
        "https://raw.githubusercontent.com/Materials-Consortia/OPTiMaDe/develop/providers.json"
    ).json()

    providers_list = []
    for provider in mat_consortia_providers.get("data", []):
        # Remove/skip "exmpl"
        if provider["id"] == "exmpl":
            continue

        provider["task_id"] = provider.pop("id")
        provider.update(provider.pop("attributes"))

        # Create MongoDB id
        oid = provider["task_id"] + provider["type"]
        if len(oid) < 12:
            oid = oid + "0" * (12 - len(oid))
        elif len(oid) > 12:
            oid = oid[:12]
        oid = oid.encode("UTF-8")
        provider["_id"] = {"$oid": ObjectId(oid)}

        providers_list.append(provider)

    return providers_list
