from pydantic import Schema, BaseModel, UrlStr, validator
from typing import List, Optional

from .entries import EntryResource, EntryResourceAttributes


__all__ = ("Person", "ReferenceResourceAttributes", "ReferenceResource")


class Person(BaseModel):
    name: str = Schema(..., decsription="""Full name of the person, REQUIRED.""")
    firstname: Optional[str] = Schema(..., description="""First name of the person.""")
    lastname: Optional[str] = Schema(..., description="""Last name of the person.""")


class ReferenceResourceAttributes(EntryResourceAttributes):
    """ Model that stores the attributes of a reference. Many properties match the
    meaning described in the
    [BibTeX specification](http://bibtexml.sourceforge.net/btxdoc.pdf).

    """

    authors: Optional[List[Person]] = Schema(
        ...,
        description="List of person objects containing the authors of the reference.",
    )
    editors: Optional[List[Person]] = Schema(
        ...,
        description="List of person objects containing the editors of the reference.",
    )

    doi: Optional[str] = Schema(
        ..., description="The digital object identifier of the reference."
    )

    url: Optional[UrlStr] = Schema(..., description="The URL of the reference.")

    address: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    annote: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    booktitle: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    chapter: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    crossref: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    edition: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    howpublished: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    institution: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    journal: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    key: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    month: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    note: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    number: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    organization: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    pages: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    publisher: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    school: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    series: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    title: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    bib_type: Optional[str] = Schema(
        ...,
        description="Type of the reference, corresponding to the **type** property in the BiBTeX specification.",
    )
    volume: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )
    year: Optional[str] = Schema(
        ..., description="Meaning of property matches the BiBTeX specification."
    )


class ReferenceResource(EntryResource):
    """ The :entry:`references` entries describe bibliographic references.
The following properties are used to provide the bibliographic details:

- **address**, **annote**, **booktitle**, **chapter**, **crossref**, **edition**, **howpublished**, **institution**, **journal**, **key**, **month**,
  **note**, **number**, **organization**, **pages**, **publisher**, **school**, **series**, **title**, **type**, **volume**, **year**:
  Meanings of these properties match the `BibTeX specification <http://bibtexml.sourceforge.net/btxdoc.pdf>`__, values are strings;

- **authors** and **editors**: lists of *person objects* which are dictionaries with the following keys:

  - **name**: Full name of the person, REQUIRED.
  - **firstname**, **lastname**: Parts of the person's name, OPTIONAL.

- **doi** and **url**: values are strings.

- **Requirements/Conventions**:

  - **Response**: Every references entry MUST contain at least one of the properties.
  - **Query**: Support for queries on any of these properties is OPTIONAL.
    If supported, filters MAY support only a subset of comparison operators. """

    type: str = Schema(
        default="references",
        const=True,
        description="""The name of the type of an entry. Any entry MUST be able to be fetched using the `base URL <Base URL_>`_ type and ID at the url :endpoint:`<base URL>/<type>/<id>`.
- **Type**: string.
- **Requirements/Conventions**:

  - **Response**: REQUIRED in the response unless explicitly excluded.
  - **Query**: Support for queries on this property is OPTIONAL.
    If supported, only a subset of string comparison operators MAY be supported.

- **Requirements/Conventions**: MUST be an existing entry type.
- **Example**: :val:`"structures"`""",
    )
    attributes: ReferenceResourceAttributes

    @validator("attributes")
    def validate_attributes(cls, v):
        if not any(prop[1] is not None for prop in v):
            raise ValueError(f"reference object must have at least one field defined")
        return v
