from typing import TYPE_CHECKING, List
from uuid import UUID

import strawberry
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
)
from yak_server.helpers.group_position import compute_group_rank

from .bearer_authentication import is_authenticated
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
    User,
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

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.orm import Session

    from yak_server.helpers.settings import Settings


@strawberry.type
class Query:
    @strawberry.field
    @is_authenticated
    def current_user_result(self, info: Info) -> CurrentUserResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        return User.from_instance(db=db, instance=user, lock_datetime=settings.lock_datetime)

    @strawberry.field
    @is_authenticated
    def all_teams_result(self, info: Info) -> AllTeamsResult:
        db: Session = info.context.db

        return AllTeamsSuccessful(
            teams=[Team.from_instance(instance=team) for team in db.query(TeamModel).all()],
        )

    @strawberry.field
    @is_authenticated
    def team_by_id_result(self, id: UUID, info: Info) -> TeamByIdResult:
        db: Session = info.context.db

        team_record = db.query(TeamModel).filter_by(id=str(id)).first()

        if not team_record:
            return TeamByIdNotFound(id=id)

        return Team.from_instance(instance=team_record)

    @strawberry.field
    @is_authenticated
    def team_by_code_result(self, code: str, info: Info) -> TeamByCodeResult:
        db: Session = info.context.db

        team_record = db.query(TeamModel).filter_by(code=code).first()

        if not team_record:
            return TeamByCodeNotFound(code=code)

        return Team.from_instance(instance=team_record)

    @strawberry.field
    @is_authenticated
    def score_bet_result(self, id: UUID, info: Info) -> ScoreBetResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        score_bet_record = db.query(ScoreBetModel).filter_by(id=str(id), user_id=user.id).first()

        if not score_bet_record:
            return ScoreBetNotFound(id=id)

        return ScoreBet.from_instance(
            db=db,
            instance=score_bet_record,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def binary_bet_result(self, id: UUID, info: Info) -> BinaryBetResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        binary_bet_record = db.query(BinaryBetModel).filter_by(id=str(id), user_id=user.id).first()

        if not binary_bet_record:
            return BinaryBetNotFound(id=id)

        return BinaryBet.from_instance(
            db=db,
            instance=binary_bet_record,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def all_groups_result(self, info: Info) -> AllGroupsResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        return Groups(
            groups=[
                Group.from_instance(
                    db=db,
                    instance=group,
                    user_id=user.id,
                    lock_datetime=settings.lock_datetime,
                )
                for group in db.query(GroupModel).order_by(GroupModel.index)
            ],
        )

    @strawberry.field
    @is_authenticated
    def group_by_id_result(self, id: UUID, info: Info) -> GroupByIdResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        group_record = db.query(GroupModel).filter_by(id=str(id)).first()

        if not group_record:
            return GroupByIdNotFound(id=id)

        return Group.from_instance(
            db=db,
            instance=group_record,
            user_id=user.id,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def group_by_code_result(self, code: strawberry.ID, info: Info) -> GroupByCodeResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        group_record = db.query(GroupModel).filter_by(code=code).first()

        if not group_record:
            return GroupByCodeNotFound(code=code)

        return Group.from_instance(
            db=db,
            instance=group_record,
            user_id=user.id,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def all_phases_result(self, info: Info) -> AllPhasesResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        phases = db.query(PhaseModel).order_by(PhaseModel.index)

        return Phases(
            phases=[
                Phase.from_instance(
                    db=db,
                    instance=phase,
                    user_id=user.id,
                    lock_datetime=settings.lock_datetime,
                )
                for phase in phases
            ],
        )

    @strawberry.field
    @is_authenticated
    def phase_by_id_result(self, id: UUID, info: Info) -> PhaseByIdResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        phase_record = db.query(PhaseModel).filter_by(id=str(id)).first()

        if not phase_record:
            return PhaseByIdNotFound(id=id)

        return Phase.from_instance(
            db=db,
            instance=phase_record,
            user_id=user.id,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def phase_by_code_result(self, code: str, info: Info) -> PhaseByCodeResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        phase_record = db.query(PhaseModel).filter_by(code=code).first()

        if not phase_record:
            return PhaseByCodeNotFound(code=code)

        return Phase.from_instance(
            db=db,
            instance=phase_record,
            user_id=user.id,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def score_board_result(self, info: Info) -> ScoreBoardResult:
        db: Session = info.context.db

        users = (
            db.query(UserModel).filter(UserModel.name != "admin").order_by(UserModel.points.desc())
        )

        return ScoreBoard(
            users=[UserWithoutSensitiveInfo.from_instance(instance=user) for user in users],
        )

    @strawberry.field
    @is_authenticated
    def group_rank_by_code_result(self, code: str, info: Info) -> GroupRankByCodeResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        group = db.query(GroupModel).filter_by(code=code).first()

        if not group:
            return GroupByCodeNotFound(code=code)

        group_rank = db.query(GroupPositionModel).filter_by(
            user_id=user.id,
            group_id=group.id,
        )

        def send_response(
            db: "Session",
            user_id: UUID,
            group: GroupModel,
            group_rank: List[GroupPositionModel],
            lock_datetime: "datetime",
        ) -> GroupRank:
            return GroupRank(
                group_rank=send_group_position(group_rank),
                group=Group.from_instance(
                    db=db,
                    instance=group,
                    user_id=user_id,
                    lock_datetime=lock_datetime,
                ),
            )

        if not any(group_position.need_recomputation for group_position in group_rank):
            return send_response(db, user.id, group, group_rank, settings.lock_datetime)

        score_bets = user.score_bets.filter(MatchModel.group_id == group.id).join(
            ScoreBetModel.match,
        )
        group_rank = compute_group_rank(group_rank, score_bets)
        db.commit()

        return send_response(db, user.id, group, group_rank, settings.lock_datetime)

    @strawberry.field
    @is_authenticated
    def group_rank_by_id_result(self, id: UUID, info: Info) -> GroupRankByIdResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        group = db.query(GroupModel).filter_by(id=str(id)).first()

        if not group:
            return GroupByIdNotFound(id=id)

        group_rank = db.query(GroupPositionModel).filter_by(
            user_id=user.id,
            group_id=group.id,
        )

        def send_response(
            db: "Session",
            user_id: UUID,
            group: GroupModel,
            group_rank: List[GroupPositionModel],
            lock_datetime: "datetime",
        ) -> GroupRank:
            return GroupRank(
                group_rank=send_group_position(group_rank),
                group=Group.from_instance(
                    db=db,
                    instance=group,
                    user_id=user_id,
                    lock_datetime=lock_datetime,
                ),
            )

        if not any(group_position.need_recomputation for group_position in group_rank):
            return send_response(db, user.id, group, group_rank, settings.lock_datetime)

        score_bets = user.score_bets.filter(MatchModel.group_id == group.id).join(
            ScoreBetModel.match,
        )
        group_rank = compute_group_rank(group_rank, score_bets)
        db.commit()

        return send_response(db, user.id, group, group_rank, settings.lock_datetime)
