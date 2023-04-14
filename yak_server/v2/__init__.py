import strawberry
from strawberry.extensions import QueryDepthLimiter

from .mutation import Mutation
from .query import Query

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[QueryDepthLimiter(max_depth=6)],
)
