from uuid import UUID

import strawberry
from sqlalchemy import and_
from strawberry.types import Info

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
    get_db,
)
from yak_server.helpers.group_position import compute_group_rank

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
    Phase,
    ScoreBet,
    Team,
    UserWithoutSensitiveInfo,
    send_group_position,
)


@strawberry.type
class Query:
    @strawberry.field
    @is_authentificated
    def current_user_result(self, info: Info) -> CurrentUserResult:
        return info.user

    @strawberry.field
    @is_authentificated
    def all_teams_result(self, info: Info) -> AllTeamsResult:  # noqa: ARG002
        db = get_db()

        return AllTeamsSuccessful(
            teams=[Team.from_instance(instance=team) for team in db.query(TeamModel).all()],
        )

    @strawberry.field
    @is_authentificated
    def team_by_id_result(self, id: UUID, info: Info) -> TeamByIdResult:  # noqa: ARG002
        db = get_db()

        team_record = db.query(TeamModel).filter_by(id=str(id)).first()

        if not team_record:
            return TeamByIdNotFound(id=id)

        return Team.from_instance(instance=team_record)

    @strawberry.field
    @is_authentificated
    def team_by_code_result(self, code: str, info: Info) -> TeamByCodeResult:  # noqa: ARG002
        db = get_db()

        team_record = db.query(TeamModel).filter_by(code=code).first()

        if not team_record:
            return TeamByCodeNotFound(code=code)

        return Team.from_instance(instance=team_record)

    @strawberry.field
    @is_authentificated
    def score_bet_result(self, id: UUID, info: Info) -> ScoreBetResult:
        db = get_db()

        score_bet_record = (
            db.query(ScoreBetModel)
            .filter_by(
                id=str(id),
                user_id=info.user.instance.id,
            )
            .first()
        )

        if not score_bet_record:
            return ScoreBetNotFound(id=id)

        return ScoreBet.from_instance(instance=score_bet_record)

    @strawberry.field
    @is_authentificated
    def binary_bet_result(self, id: UUID, info: Info) -> BinaryBetResult:
        db = get_db()

        binary_bet_record = (
            db.query(BinaryBetModel)
            .filter_by(
                id=str(id),
                user_id=info.user.instance.id,
            )
            .first()
        )

        if not binary_bet_record:
            return BinaryBetNotFound(id=id)

        return BinaryBet.from_instance(instance=binary_bet_record)

    @strawberry.field
    @is_authentificated
    def all_groups_result(self, info: Info) -> AllGroupsResult:
        db = get_db()

        return Groups(
            groups=[
                Group.from_instance(instance=group, user_id=info.user.instance.id)
                for group in db.query(GroupModel).order_by(GroupModel.index)
            ],
        )

    @strawberry.field
    @is_authentificated
    def group_by_id_result(self, id: UUID, info: Info) -> GroupByIdResult:
        db = get_db()

        group_record = db.query(GroupModel).filter_by(id=str(id)).first()

        if not group_record:
            return GroupByIdNotFound(id=id)

        return Group.from_instance(instance=group_record, user_id=info.user.instance.id)

    @strawberry.field
    @is_authentificated
    def group_by_code_result(self, code: strawberry.ID, info: Info) -> GroupByCodeResult:
        db = get_db()

        group_record = db.query(GroupModel).filter_by(code=code).first()

        if not group_record:
            return GroupByCodeNotFound(code=code)

        return Group.from_instance(instance=group_record, user_id=info.user.instance.id)

    @strawberry.field
    @is_authentificated
    def all_phases_result(self, info: Info) -> AllPhasesResult:
        db = get_db()

        phases = db.query(PhaseModel).order_by(PhaseModel.index)

        return Phases(
            phases=[
                Phase.from_instance(instance=phase, user_id=info.user.instance.id)
                for phase in phases
            ],
        )

    @strawberry.field
    @is_authentificated
    def phase_by_id_result(self, id: UUID, info: Info) -> PhaseByIdResult:
        db = get_db()

        phase_record = db.query(PhaseModel).filter_by(id=str(id)).first()

        if not phase_record:
            return PhaseByIdNotFound(id=id)

        return Phase.from_instance(instance=phase_record, user_id=info.user.instance.id)

    @strawberry.field
    @is_authentificated
    def phase_by_code_result(self, code: str, info: Info) -> PhaseByCodeResult:
        db = get_db()

        phase_record = db.query(PhaseModel).filter_by(code=code).first()

        if not phase_record:
            return PhaseByCodeNotFound(code=code)

        return Phase.from_instance(instance=phase_record, user_id=info.user.instance.id)

    @strawberry.field
    @is_authentificated
    def score_board_result(self, info: Info) -> ScoreBoardResult:  # noqa: ARG002
        db = get_db()

        users = db.query(UserModel).filter(UserModel.name != "admin")

        return ScoreBoard(
            users=[UserWithoutSensitiveInfo.from_instance(instance=user) for user in users],
        )

    @strawberry.field
    @is_authentificated
    def group_rank_by_code_result(self, code: str, info: Info) -> GroupRankByCodeResult:
        db = get_db()

        group = db.query(GroupModel).filter_by(code=code).first()

        if not group:
            return GroupByCodeNotFound(code=code)

        group_rank = db.query(GroupPositionModel).filter_by(
            user_id=info.user.instance.id,
            group_id=group.id,
        )

        def send_response(user_id, group_rank):
            return GroupRank(
                group_rank=send_group_position(group_rank),
                group=Group.from_instance(instance=group, user_id=user_id),
            )

        if not any(group_position.need_recomputation for group_position in group_rank):
            return send_response(info.user.id, group_rank)

        score_bets = (
            db.query(ScoreBetModel)
            .filter(and_(ScoreBetModel.user_id == info.user.id, MatchModel.group_id == group.id))
            .join(ScoreBetModel.match)
        )

        group_rank = compute_group_rank(group_rank, score_bets)
        db.commit()

        return send_response(info.user.id, group_rank)

    @strawberry.field
    @is_authentificated
    def group_rank_by_id_result(self, id: UUID, info: Info) -> GroupRankByIdResult:
        db = get_db()

        group = db.query(GroupModel).filter_by(id=str(id)).first()

        if not group:
            return GroupByIdNotFound(id=id)

        group_rank = db.query(GroupPositionModel).filter_by(
            user_id=info.user.instance.id,
            group_id=group.id,
        )

        def send_response(user_id, group_rank):
            return GroupRank(
                group_rank=send_group_position(group_rank),
                group=Group.from_instance(instance=group, user_id=user_id),
            )

        if not any(group_position.need_recomputation for group_position in group_rank):
            return send_response(info.user.id, group_rank)

        score_bets = (
            db.query(ScoreBetModel)
            .filter(and_(ScoreBetModel.user_id == info.user.id, MatchModel.group_id == group.id))
            .join(ScoreBetModel.match)
        )
        group_rank = compute_group_rank(group_rank, score_bets)
        db.commit()

        return send_response(info.user.id, group_rank)
