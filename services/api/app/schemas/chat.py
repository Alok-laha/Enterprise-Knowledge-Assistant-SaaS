from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class QueryRequest(BaseModel):
    query: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=4000),
    ]


class QueryCitation(BaseModel):
    source_uri: str | None
    excerpt: str | None


class QueryResponse(BaseModel):
    answer: str
    citations: list[QueryCitation] = Field(default_factory=list)
