from typing import TYPE_CHECKING

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

from .bearer_authenfication import bearer_authentification
from .schema import (
    AllGroupsResult,
    AllPhasesResult,
    AllTeamsResult,
    AllTeamsSuccessful,
    BinaryBet,
    BinaryBetNotFound,
    BinaryBetResult,
    Group,
    GroupByCodeNotFound,
    GroupByCodeResult,
    GroupByIdNotFound,
    GroupByIdResult,
    Groups,
    Phase,
    PhaseByCodeNotFound,
    PhaseByCodeResult,
    PhaseByIdNotFound,
    PhaseByIdResult,
    Phases,
    ScoreBet,
    ScoreBetNotFound,
    ScoreBetResult,
    ScoreBoard,
    ScoreBoardResult,
    Team,
    TeamByCodeNotFound,
    TeamByCodeResult,
    TeamByIdNotFound,
    TeamByIdResult,
    UserResult,
    UserWithoutSensitiveInfo,
)


@strawberry.type
class Query:
    @strawberry.field
    def user_result(self) -> UserResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        return user

    @strawberry.field
    def all_teams_result(self) -> AllTeamsResult:
        _, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        return AllTeamsSuccessful(
            teams=[Team.from_instance(instance=team) for team in TeamModel.query.all()],
        )

    @strawberry.field
    def team_by_id_result(self, id: strawberry.ID) -> TeamByIdResult:
        _, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        team_record = TeamModel.query.filter_by(id=id).first()

        if not team_record:
            return TeamByIdNotFound(id=id)

        return Team.from_instance(instance=team_record)

    @strawberry.field
    def team_by_code_result(self, code: strawberry.ID) -> TeamByCodeResult:
        _, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        team_record = TeamModel.query.filter_by(code=code).first()

        if not team_record:
            return TeamByCodeNotFound(code=code)

        return Team.from_instance(instance=team_record)

    @strawberry.field
    def score_bet_result(self, id: strawberry.ID) -> ScoreBetResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        score_bet_record = ScoreBetModel.query.filter_by(
            id=id,
            user_id=user.instance.id,
        ).first()

        if not score_bet_record:
            return ScoreBetNotFound(id=id)

        return ScoreBet.from_instance(instance=score_bet_record)

    @strawberry.field
    def binary_bet_result(self, id: strawberry.ID) -> BinaryBetResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        binary_bet_record = BinaryBetModel.query.filter_by(
            id=id,
            user_id=user.instance.id,
        ).first()

        if not binary_bet_record:
            return BinaryBetNotFound(id=id)

        return BinaryBet.from_instance(instance=binary_bet_record)

    @strawberry.field
    def all_groups_result(self) -> AllGroupsResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        return Groups(
            groups=[
                Group.from_instance(instance=group, user_id=user.instance.id)
                for group in GroupModel.query.order_by(GroupModel.index)
            ],
        )

    @strawberry.field
    def group_by_id_result(self, id: strawberry.ID) -> GroupByIdResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        group_record = GroupModel.query.filter_by(id=id).first()

        if not group_record:
            return GroupByIdNotFound(id=id)

        return Group.from_instance(instance=group_record, user_id=user.instance.id)

    @strawberry.field
    def group_by_code_result(self, code: strawberry.ID) -> GroupByCodeResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        group_record = GroupModel.query.filter_by(code=code).first()

        if not group_record:
            return GroupByCodeNotFound(code=code)

        return Group.from_instance(instance=group_record, user_id=user.instance.id)

    @strawberry.field
    def all_phases_result(self) -> AllPhasesResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        phases = PhaseModel.query.order_by(PhaseModel.index)

        return Phases(
            phases=[
                Phase.from_instance(instance=phase, user_id=user.instance.id) for phase in phases
            ]
        )

    @strawberry.field
    def phase_by_id_result(self, id: strawberry.ID) -> PhaseByIdResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        phase_record = PhaseModel.query.filter_by(id=id).first()

        if not phase_record:
            return PhaseByIdNotFound(id=id)

        return Phase.from_instance(instance=phase_record, user_id=user.instance.id)

    @strawberry.field
    def phase_by_code_result(self, code: strawberry.ID) -> PhaseByCodeResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        phase_record = PhaseModel.query.filter_by(code=code).first()

        if not phase_record:
            return PhaseByCodeNotFound(code=code)

        return Phase.from_instance(instance=phase_record, user_id=user.instance.id)

    @strawberry.field
    def score_board_result(self, info: "Info") -> ScoreBoardResult:
        _, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        users = UserModel.query.filter(UserModel.name != "admin")

        return ScoreBoard(
            users=[UserWithoutSensitiveInfo.from_instance(instance=user) for user in users]
        )
