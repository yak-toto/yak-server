from typing import TYPE_CHECKING

from fastapi import FastAPI
from sqladmin import Admin, ModelView

from yak_server.database import build_engine
from yak_server.database.models import (
    GroupModel,
    PhaseModel,
    RefreshTokenModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)

if TYPE_CHECKING:
    from fastapi import FastAPI


def view_admin(app: "FastAPI") -> None:
    admin = Admin(app, build_engine())

    class UserAdmin(ModelView, model=UserModel):
        name = "Users"
        name_plural = False
        column_default_sort = "name"
        column_list = (UserModel.id, UserModel.full_name, UserModel.name)

    class GroupAdmin(ModelView, model=GroupModel):
        name = "Groups"
        name_plural = False
        column_default_sort = "index"
        column_list = (GroupModel.id, GroupModel.description_en, "phase.description_en")

    class PhaseAdmin(ModelView, model=PhaseModel):
        name = "Phases"
        name_plural = False
        column_default_sort = "index"
        column_list = (PhaseModel.id, PhaseModel.description_en)

    class TeamAdmin(ModelView, model=TeamModel):
        name = "Teams"
        name_plural = False
        column_default_sort = "description_en"
        column_list = (TeamModel.id, TeamModel.description_en)

    class RefreshTokenAdmin(ModelView, model=RefreshTokenModel):
        name = "Refresh Tokens"
        name_plural = False
        column_default_sort = "expiration"
        column_list = (
            RefreshTokenModel.id,
            "user.full_name",
            RefreshTokenModel.expiration,
        )

    class ScoreBetAdmin(ModelView, model=ScoreBetModel):
        name = "Score Bets"
        name_plural = False
        page_size = 50
        column_default_sort = [("match.group.index", False), ("match.index", False)]  # noqa: RUF012
        column_list = (
            # ScoreBetModel.id,
            "match.user.full_name",
            "match.team1.description_en",
            ScoreBetModel.score1,
            ScoreBetModel.score2,
            "match.team2.description_en",
            "match.group.description_en",
            "match.group.phase.description_en",
        )

    admin.add_view(UserAdmin)
    admin.add_view(GroupAdmin)
    admin.add_view(RefreshTokenAdmin)
    admin.add_view(PhaseAdmin)
    admin.add_view(TeamAdmin)
    admin.add_view(ScoreBetAdmin)
