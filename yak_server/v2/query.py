from typing import TYPE_CHECKING
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
)
from yak_server.helpers.group_position import compute_group_rank
from yak_server.helpers.password_validator import PasswordRequirements

from .bearer_authentication import is_authenticated
from .context import YakContext
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
    PasswordRequirementsResult,
    Phase,
    ScoreBet,
    Team,
    User,
    UserWithoutSensitiveInfo,
    send_group_position,
)

if TYPE_CHECKING:
    import pendulum
    from sqlalchemy.orm import Session


@strawberry.type
class Query:
    @strawberry.field
    @is_authenticated
    def current_user_result(self, info: Info[YakContext, None]) -> CurrentUserResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        return User.from_instance(user, db=db, lock_datetime=settings.lock_datetime)

    @strawberry.field
    def password_requirements(self) -> PasswordRequirementsResult:
        password_requirements = PasswordRequirements()

        return PasswordRequirementsResult(
            minimum_length=password_requirements.MINIMUM_LENGTH,
            uppercase=password_requirements.UPPERCASE,
            lowercase=password_requirements.LOWERCASE,
            digit=password_requirements.DIGIT,
            no_space=password_requirements.NO_SPACE,
        )

    @strawberry.field
    @is_authenticated
    def all_teams_result(self, info: Info[YakContext, None]) -> AllTeamsResult:
        db = info.context.db

        return AllTeamsSuccessful(
            teams=[Team.from_instance(team) for team in db.query(TeamModel).all()]
        )

    @strawberry.field
    @is_authenticated
    def team_by_id_result(self, id: UUID, info: Info[YakContext, None]) -> TeamByIdResult:
        db = info.context.db

        team_record = db.query(TeamModel).filter_by(id=id).first()

        if not team_record:
            return TeamByIdNotFound(id=id)

        return Team.from_instance(team_record)

    @strawberry.field
    @is_authenticated
    def team_by_code_result(self, code: str, info: Info[YakContext, None]) -> TeamByCodeResult:
        db = info.context.db

        team_record = db.query(TeamModel).filter_by(code=code).first()

        if not team_record:
            return TeamByCodeNotFound(code=code)

        return Team.from_instance(team_record)

    @strawberry.field
    @is_authenticated
    def score_bet_result(self, id: UUID, info: Info[YakContext, None]) -> ScoreBetResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        score_bet_record = (
            db.query(ScoreBetModel)
            .join(ScoreBetModel.match)
            .filter(and_(ScoreBetModel.id == id, MatchModel.user_id == user.id))
            .first()
        )

        if not score_bet_record:
            return ScoreBetNotFound(id=id)

        return ScoreBet.from_instance(score_bet_record, db=db, lock_datetime=settings.lock_datetime)

    @strawberry.field
    @is_authenticated
    def binary_bet_result(self, id: UUID, info: Info[YakContext, None]) -> BinaryBetResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        binary_bet_record = (
            db.query(BinaryBetModel)
            .join(BinaryBetModel.match)
            .filter(and_(BinaryBetModel.id == id, MatchModel.user_id == user.id))
            .first()
        )

        if not binary_bet_record:
            return BinaryBetNotFound(id=id)

        return BinaryBet.from_instance(
            binary_bet_record, db=db, lock_datetime=settings.lock_datetime
        )

    @strawberry.field
    @is_authenticated
    def all_groups_result(self, info: Info[YakContext, None]) -> AllGroupsResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        return Groups(
            groups=[
                Group.from_instance(
                    group,
                    db=db,
                    user=user,
                    lock_datetime=settings.lock_datetime,
                )
                for group in db.query(GroupModel).order_by(GroupModel.index)
            ],
        )

    @strawberry.field
    @is_authenticated
    def group_by_id_result(self, id: UUID, info: Info[YakContext, None]) -> GroupByIdResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        group_record = db.query(GroupModel).filter_by(id=id).first()

        if not group_record:
            return GroupByIdNotFound(id=id)

        return Group.from_instance(
            group_record,
            db=db,
            user=user,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def group_by_code_result(
        self,
        code: strawberry.ID,
        info: Info[YakContext, None],
    ) -> GroupByCodeResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        group_record = db.query(GroupModel).filter_by(code=code).first()

        if not group_record:
            return GroupByCodeNotFound(code=code)

        return Group.from_instance(
            group_record,
            db=db,
            user=user,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def all_phases_result(self, info: Info[YakContext, None]) -> AllPhasesResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        phases = db.query(PhaseModel).order_by(PhaseModel.index)

        return Phases(
            phases=[
                Phase.from_instance(
                    phase,
                    db=db,
                    user=user,
                    lock_datetime=settings.lock_datetime,
                )
                for phase in phases
            ],
        )

    @strawberry.field
    @is_authenticated
    def phase_by_id_result(self, id: UUID, info: Info[YakContext, None]) -> PhaseByIdResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        phase_record = db.query(PhaseModel).filter_by(id=id).first()

        if not phase_record:
            return PhaseByIdNotFound(id=id)

        return Phase.from_instance(
            phase_record,
            db=db,
            user=user,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def phase_by_code_result(self, code: str, info: Info[YakContext, None]) -> PhaseByCodeResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        phase_record = db.query(PhaseModel).filter_by(code=code).first()

        if not phase_record:
            return PhaseByCodeNotFound(code=code)

        return Phase.from_instance(
            phase_record,
            db=db,
            user=user,
            lock_datetime=settings.lock_datetime,
        )

    @strawberry.field
    @is_authenticated
    def score_board_result(self, info: Info[YakContext, None]) -> ScoreBoardResult:
        db = info.context.db

        users = (
            db.query(UserModel).filter(UserModel.name != "admin").order_by(UserModel.points.desc())
        )

        return ScoreBoard(
            users=[UserWithoutSensitiveInfo.from_instance(user) for user in users],
        )

    @strawberry.field
    @is_authenticated
    def group_rank_by_code_result(
        self,
        code: str,
        info: Info[YakContext, None],
    ) -> GroupRankByCodeResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        group = db.query(GroupModel).filter_by(code=code).first()

        if not group:
            return GroupByCodeNotFound(code=code)

        group_rank = db.query(GroupPositionModel).filter_by(
            user_id=user.id,
            group_id=group.id,
        )

        def send_response(
            db: "Session",
            user: UserModel,
            group: GroupModel,
            group_rank: list[GroupPositionModel],
            lock_datetime: "pendulum.DateTime",
        ) -> GroupRank:
            return GroupRank(
                group_rank=send_group_position(group_rank),
                group=Group.from_instance(
                    group,
                    db=db,
                    user=user,
                    lock_datetime=lock_datetime,
                ),
            )

        if not any(group_position.need_recomputation for group_position in group_rank):
            return send_response(db, user, group, group_rank, settings.lock_datetime)

        score_bets = (
            db.query(ScoreBetModel)
            .join(ScoreBetModel.match)
            .filter(and_(MatchModel.user_id == user.id, MatchModel.group_id == group.id))
        )
        group_rank = compute_group_rank(group_rank, score_bets)
        db.commit()

        return send_response(db, user, group, group_rank, settings.lock_datetime)

    @strawberry.field
    @is_authenticated
    def group_rank_by_id_result(
        self,
        id: UUID,
        info: Info[YakContext, None],
    ) -> GroupRankByIdResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        group = db.query(GroupModel).filter_by(id=id).first()

        if not group:
            return GroupByIdNotFound(id=id)

        group_rank = db.query(GroupPositionModel).filter_by(
            user_id=user.id,
            group_id=group.id,
        )

        def send_response(
            db: "Session",
            user: UserModel,
            group: GroupModel,
            group_rank: list[GroupPositionModel],
            lock_datetime: "pendulum.DateTime",
        ) -> GroupRank:
            return GroupRank(
                group_rank=send_group_position(group_rank),
                group=Group.from_instance(
                    group,
                    db=db,
                    user=user,
                    lock_datetime=lock_datetime,
                ),
            )

        if not any(group_position.need_recomputation for group_position in group_rank):
            return send_response(db, user, group, group_rank, settings.lock_datetime)

        score_bets = (
            db.query(ScoreBetModel)
            .join(ScoreBetModel.match)
            .filter(and_(MatchModel.user_id == user.id, MatchModel.group_id == group.id))
        )
        group_rank = compute_group_rank(group_rank, score_bets)
        db.commit()

        return send_response(db, user, group, group_rank, settings.lock_datetime)
