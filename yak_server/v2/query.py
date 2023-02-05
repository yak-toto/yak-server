from typing import TYPE_CHECKING, Optional

import strawberry

if TYPE_CHECKING:
    from strawberry.types import Info

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)

from .bearer_authenfication import BearerAuthentification, bearer_authentification
from .schema import (
    AllTeamsResponse,
    BinaryBet,
    GetUserResponse,
    Group,
    Phase,
    ScoreBet,
    Team,
    UserWithoutSensitiveInfo,
)


@strawberry.type
class Query:
    @strawberry.field
    def get_user(self) -> GetUserResponse:
        user, errors = bearer_authentification()

        return GetUserResponse(user=user, errors=errors)

    @strawberry.field
    def all_teams(self) -> AllTeamsResponse:
        _, errors = bearer_authentification()

        if not errors:
            teams = TeamModel.query.all()
            return AllTeamsResponse(
                teams=[Team.from_instance(instance=team) for team in teams],
                errors=None,
            )

        else:
            return AllTeamsResponse(teams=None, errors=errors)

    @strawberry.field(permission_classes=[BearerAuthentification])
    def team_by_id(self, id: strawberry.ID) -> Optional[Team]:
        team_record = TeamModel.query.filter_by(id=id).first()

        if not team_record:
            return None

        return Team.from_instance(instance=team_record)

    @strawberry.field(permission_classes=[BearerAuthentification])
    def team_by_code(self, code: strawberry.ID) -> Optional[Team]:
        team_record = TeamModel.query.filter_by(code=code).first()

        if not team_record:
            return None

        return Team.from_instance(instance=team_record)

    @strawberry.field(permission_classes=[BearerAuthentification])
    def score_bet(self, id: strawberry.ID, info: "Info") -> Optional[ScoreBet]:
        score_bet_record = ScoreBetModel.query.filter_by(
            id=id,
            user_id=info.user.id,
        ).first()

        if not score_bet_record:
            return None

        return ScoreBet.from_instance(instance=score_bet_record)

    @strawberry.field(permission_classes=[BearerAuthentification])
    def binary_bet(self, id: strawberry.ID, info: "Info") -> Optional[BinaryBet]:
        binary_bet_record = BinaryBetModel.query.filter_by(
            id=id,
            user_id=info.user.id,
        ).first()

        if not binary_bet_record:
            return None

        return BinaryBet.from_instance(instance=binary_bet_record)

    @strawberry.field(permission_classes=[BearerAuthentification])
    def all_groups(self, info: "Info") -> list[Group]:
        groups = GroupModel.query.all()

        return [Group.from_instance(instance=group, user_id=info.user.id) for group in groups]

    @strawberry.field(permission_classes=[BearerAuthentification])
    def group_by_id(self, id: strawberry.ID, info: "Info") -> Optional[Group]:
        group_record = GroupModel.query.filter_by(id=id).first()

        if not group_record:
            return None

        return Group.from_instance(instance=group_record, user_id=info.user.id)

    @strawberry.field(permission_classes=[BearerAuthentification])
    def group_by_code(self, code: strawberry.ID, info: "Info") -> Optional[Group]:
        group_record = GroupModel.query.filter_by(code=code).first()

        if not group_record:
            return None

        return Group.from_instance(instance=group_record, user_id=info.user.id)

    @strawberry.field(permission_classes=[BearerAuthentification])
    def all_phases(self, info: "Info") -> list[Phase]:
        phases = PhaseModel.query.all()

        return [Phase.from_instance(instance=phase, user_id=info.user.id) for phase in phases]

    @strawberry.field(permission_classes=[BearerAuthentification])
    def phase_by_id(self, id: strawberry.ID, info: "Info") -> Optional[Phase]:
        phase_record = PhaseModel.query.filter_by(id=id).first()

        if not phase_record:
            return None

        return Phase.from_instance(instance=phase_record, user_id=info.user.id)

    @strawberry.field(permission_classes=[BearerAuthentification])
    def phase_by_code(self, code: strawberry.ID, info: "Info") -> Optional[Phase]:
        phase_record = PhaseModel.query.filter_by(code=code).first()

        if not phase_record:
            return None

        return Phase.from_instance(instance=phase_record, user_id=info.user.id)

    @strawberry.field(permission_classes=[BearerAuthentification])
    def score_board(self, info: "Info") -> list[UserWithoutSensitiveInfo]:
        users = UserModel.query.filter(UserModel.name != "admin")

        return [UserWithoutSensitiveInfo.from_instance(instance=user) for user in users]
