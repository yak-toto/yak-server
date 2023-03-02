import strawberry
from flask import current_app
from strawberry.extensions import MaskErrors, QueryDepthLimiter

from .mutation import Mutation
from .query import Query


def mask_errors(_) -> bool:
    return not current_app.config["DEBUG"]


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[MaskErrors(should_mask_error=mask_errors), QueryDepthLimiter(max_depth=6)],
)
