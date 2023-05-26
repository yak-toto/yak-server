import strawberry
from graphql.validation import NoSchemaIntrospectionCustomRule
from strawberry.extensions import (
    AddValidationRules,
    MaxAliasesLimiter,
    MaxTokensLimiter,
    ParserCache,
    QueryDepthLimiter,
    ValidationCache,
)

from .mutation import Mutation
from .query import Query


def get_schema(debug: bool) -> strawberry.Schema:
    extensions = [
        QueryDepthLimiter(max_depth=6),
        MaxAliasesLimiter(max_alias_count=30),
        MaxTokensLimiter(max_token_count=500),
        ValidationCache(),
        ParserCache(),
    ]

    if not debug:
        extensions.append(AddValidationRules([NoSchemaIntrospectionCustomRule]))

    return strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=extensions,
    )
