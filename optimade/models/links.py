from pydantic import Schema, UrlStr, validator  # pylint: disable=no-name-in-module
from typing import Union

from .jsonapi import Link, Attributes
from .entries import EntryResource


__all__ = (
    "LinksResourceAttributes",
    "LinksResource",
    "ChildResource",
    "ParentResource",
    "ProviderResource",
)


class LinksResourceAttributes(Attributes):
    """Links endpoint resource object attributes"""

    name: str = Schema(
        ...,
        description="Human-readable name for the OPTiMaDe API implementation "
        "a client may provide in a list to an end-user.",
    )
    description: str = Schema(
        ...,
        description="Human-readable description for the OPTiMaDe API implementation "
        "a client may provide in a list to an end-user.",
    )
    base_url: Union[UrlStr, Link, None] = Schema(
        ...,
        description="JSON API links object, pointing to the base URL for this implementation",
    )


class LinksResource(EntryResource):
    """A Links endpoint resource object"""

    type: str = Schema(
        ...,
        description='MUST be either "parent", "child", or "provider". '
        "These objects are described in detail in sections Parent and Child Objects "
        "and Provider Objects.",
    )

    attributes: LinksResourceAttributes = Schema(
        ...,
        description="a dictionary containing key-value pairs representing the "
        "entry's properties.",
    )

    @validator("type")
    def type_must_be_in_specific_set(cls, value):
        if value not in {"parent", "child", "provider"}:
            raise ValueError(
                "name of Links endpoint resource MUST be either 'parent, 'child', or 'provider'"
            )
        return value

    @validator("relationships")
    def relationships_must_not_be_present(cls, value):
        raise ValueError('"relationships" is not allowed for links resources')


class ChildResource(LinksResource):
    """A child object representing a link to an implementation exactly one layer below the current implementation"""

    type: str = Schema("child", const=True)


class ParentResource(LinksResource):
    """A parent object representing a link to an implementation exactly one layer above the current implementation"""

    type: str = Schema("parent", const=True)


class ProviderResource(LinksResource):
    """A provider object representing a link to another index meta-database by another database provider"""

    type: str = Schema("provider", const=True)
