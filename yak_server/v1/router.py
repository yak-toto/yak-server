from fastapi import APIRouter

from yak_server.v1.helpers.responses import VALIDATION_ERROR_RESPONSE

from .routers import (
    bets,
    binary_bets,
    competition,
    groups,
    phases,
    results,
    rules,
    score_bets,
    teams,
    users,
)

router = APIRouter(prefix="/v1", responses=VALIDATION_ERROR_RESPONSE)

for sub_router in (
    bets.router,
    binary_bets.router,
    competition.router,
    groups.router,
    phases.router,
    results.router,
    rules.router,
    score_bets.router,
    teams.router,
    users.router,
):
    router.include_router(sub_router)
