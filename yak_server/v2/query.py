from uuid import UUID

import strawberry
from strawberry.types import Info

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)

from .bearer_authenfication import is_authentificated
from .result import (
    AllGroupsResult,
    AllPhasesResult,
    AllTeamsResult,
    AllTeamsSuccessful,
    BinaryBetNotFound,
    BinaryBetResult,
    CurrentUserResult,
    GroupByCodeNotFound,
    GroupByCodeResult,
    GroupByIdNotFound,
    GroupByIdResult,
    GroupRank,
    GroupRankByCodeResult,
    GroupRankByIdResult,
    Groups,
    PhaseByCodeNotFound,
    PhaseByCodeResult,
    PhaseByIdNotFound,
    PhaseByIdResult,
    Phases,
    ScoreBetNotFound,
    ScoreBetResult,
    ScoreBoard,
    ScoreBoardResult,
    TeamByCodeNotFound,
    TeamByCodeResult,
    TeamByIdNotFound,
    TeamByIdResult,
)
from .schema import (
    BinaryBet,
    Group,
    GroupPosition,
    Phase,
    ScoreBet,
    Team,
    UserWithoutSensitiveInfo,
)


@strawberry.type
class Query:
    @strawberry.field
    @is_authentificated
    def current_user_result(self, info: Info) -> CurrentUserResult:
        return info.user

    @strawberry.field
    @is_authentificated
    def all_teams_result(self, info: Info) -> AllTeamsResult:
        return AllTeamsSuccessful(
            teams=[Team.from_instance(instance=team) for team in TeamModel.query.all()],
        )

    @strawberry.field
    @is_authentificated
    def team_by_id_result(self, id: UUID, info: Info) -> TeamByIdResult:
        team_record = TeamModel.query.filter_by(id=str(id)).first()

        if not team_record:
            return TeamByIdNotFound(id=id)

        return Team.from_instance(instance=team_record)

    @strawberry.field
    @is_authentificated
    def team_by_code_result(self, code: str, info: Info) -> TeamByCodeResult:
        team_record = TeamModel.query.filter_by(code=code).first()

        if not team_record:
            return TeamByCodeNotFound(code=code)

        return Team.from_instance(instance=team_record)

    @strawberry.field
    @is_authentificated
    def score_bet_result(self, id: UUID, info: Info) -> ScoreBetResult:
        score_bet_record = ScoreBetModel.query.filter_by(
            id=str(id),
            user_id=info.user.instance.id,
        ).first()

        if not score_bet_record:
            return ScoreBetNotFound(id=id)

        return ScoreBet.from_instance(instance=score_bet_record)

    @strawberry.field
    @is_authentificated
    def binary_bet_result(self, id: UUID, info: Info) -> BinaryBetResult:
        binary_bet_record = BinaryBetModel.query.filter_by(
            id=str(id),
            user_id=info.user.instance.id,
        ).first()

        if not binary_bet_record:
            return BinaryBetNotFound(id=id)

        return BinaryBet.from_instance(instance=binary_bet_record)

    @strawberry.field
    @is_authentificated
    def all_groups_result(self, info: Info) -> AllGroupsResult:
        return Groups(
            groups=[
                Group.from_instance(instance=group, user_id=info.user.instance.id)
                for group in GroupModel.query.order_by(GroupModel.index)
            ],
        )

    @strawberry.field
    @is_authentificated
    def group_by_id_result(self, id: UUID, info: Info) -> GroupByIdResult:
        group_record = GroupModel.query.filter_by(id=str(id)).first()

        if not group_record:
            return GroupByIdNotFound(id=id)

        return Group.from_instance(instance=group_record, user_id=info.user.instance.id)

    @strawberry.field
    @is_authentificated
    def group_by_code_result(self, code: strawberry.ID, info: Info) -> GroupByCodeResult:
        group_record = GroupModel.query.filter_by(code=code).first()

        if not group_record:
            return GroupByCodeNotFound(code=code)

        return Group.from_instance(instance=group_record, user_id=info.user.instance.id)

    @strawberry.field
    @is_authentificated
    def all_phases_result(self, info: Info) -> AllPhasesResult:
        phases = PhaseModel.query.order_by(PhaseModel.index)

        return Phases(
            phases=[
                Phase.from_instance(instance=phase, user_id=info.user.instance.id)
                for phase in phases
            ],
        )

    @strawberry.field
    @is_authentificated
    def phase_by_id_result(self, id: UUID, info: Info) -> PhaseByIdResult:
        phase_record = PhaseModel.query.filter_by(id=str(id)).first()

        if not phase_record:
            return PhaseByIdNotFound(id=id)

        return Phase.from_instance(instance=phase_record, user_id=info.user.instance.id)

    @strawberry.field
    @is_authentificated
    def phase_by_code_result(self, code: str, info: Info) -> PhaseByCodeResult:
        phase_record = PhaseModel.query.filter_by(code=code).first()

        if not phase_record:
            return PhaseByCodeNotFound(code=code)

        return Phase.from_instance(instance=phase_record, user_id=info.user.instance.id)

    @strawberry.field
    @is_authentificated
    def score_board_result(self, info: Info) -> ScoreBoardResult:
        users = UserModel.query.filter(UserModel.name != "admin")

        return ScoreBoard(
            users=[UserWithoutSensitiveInfo.from_instance(instance=user) for user in users],
        )

    @strawberry.field
    @is_authentificated
    def group_rank_by_code_result(self, code: str, info: Info) -> GroupRankByCodeResult:
        group = GroupModel.query.filter_by(code=code).first()

        if not group:
            return GroupByCodeNotFound(code=code)

        group_rank = GroupPositionModel.query.filter_by(
            user_id=info.user.instance.id,
            group_id=group.id,
        )

        return GroupRank(
            group_rank=sorted(
                [
                    GroupPosition.from_instance(instance=group_position)
                    for group_position in group_rank
                ],
                key=lambda team: (
                    team.points(),
                    team.goals_difference(),
                    team.goals_for,
                ),
                reverse=True,
            ),
            group=Group.from_instance(instance=group, user_id=info.user.instance.id),
        )

    @strawberry.field
    @is_authentificated
    def group_rank_by_id_result(self, id: UUID, info: Info) -> GroupRankByIdResult:
        group = GroupModel.query.filter_by(id=str(id)).first()

        if not group:
            return GroupByIdNotFound(id=id)

        group_rank = GroupPositionModel.query.filter_by(
            user_id=info.user.instance.id,
            group_id=group.id,
        )

        return GroupRank(
            group_rank=sorted(
                [
                    GroupPosition.from_instance(instance=group_position)
                    for group_position in group_rank
                ],
                key=lambda team: (
                    team.points(),
                    team.goals_difference(),
                    team.goals_for,
                ),
                reverse=True,
            ),
            group=Group.from_instance(instance=group, user_id=info.user.instance.id),
        )
