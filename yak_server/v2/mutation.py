import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import strawberry
from sqlalchemy import update
from strawberry.types import Info

from yak_server.database.models import (
    BinaryBetModel,
    GroupPositionModel,
    MatchModel,
    MatchReferenceModel,
    ScoreBetModel,
    UserModel,
)
from yak_server.helpers.authentication import encode_bearer_token
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.group_position import create_group_position
from yak_server.helpers.logging import (
    logged_in_successfully,
    modify_binary_bet_successfully,
    modify_score_bet_successfully,
    signed_up_successfully,
)

from .bearer_authentication import (
    is_admin_authenticated,
    is_authenticated,
)
from .result import (
    BinaryBetNotFoundForUpdate,
    InvalidCredentials,
    LockedBinaryBetError,
    LockedScoreBetError,
    LoginResult,
    ModifyBinaryBetResult,
    ModifyScoreBetResult,
    ModifyUserResult,
    NewScoreNegative,
    ScoreBetNotFoundForUpdate,
    SignupResult,
    UserNameAlreadyExists,
    UserNotFound,
    UserWithoutSensitiveInfo,
)
from .schema import (
    BinaryBet,
    ScoreBet,
    UserWithToken,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from yak_server.helpers.settings import Settings

logger = logging.getLogger(__name__)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def signup_result(
        self,
        user_name: str,
        password: str,
        first_name: str,
        last_name: str,
        info: Info,
    ) -> SignupResult:
        db: Session = info.context.db
        settings: Settings = info.context.settings

        # Check existing user in db
        existing_user = db.query(UserModel).filter_by(name=user_name).first()
        if existing_user:
            return UserNameAlreadyExists(user_name=user_name)

        # Initialize user and integrate in db
        user = UserModel(
            name=user_name,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        db.add(user)
        db.flush()

        # Initialize matches and bets and integrate in db
        for match_reference in db.query(MatchReferenceModel).all():
            match = MatchModel(
                team1_id=match_reference.team1_id,
                team2_id=match_reference.team2_id,
                index=match_reference.index,
                group_id=match_reference.group_id,
            )
            db.add(match)
            db.flush()

            db.add(
                match_reference.bet_type_from_match.value(user_id=user.id, match_id=match.id),
            )
            db.flush()

        # Create group position records
        db.add_all(create_group_position(db.query(ScoreBetModel).filter_by(user_id=user.id)))
        db.commit()

        token = encode_bearer_token(
            sub=user.id,
            expiration_time=timedelta(seconds=settings.jwt_expiration_time),
            secret_key=settings.jwt_secret_key,
        )

        logger.info(signed_up_successfully(user.name))

        return UserWithToken.from_instance(
            db=db,
            instance=user,
            lock_datetime=settings.lock_datetime,
            token=token,
        )

    @strawberry.mutation
    def login_result(self, user_name: str, password: str, info: Info) -> LoginResult:
        db: Session = info.context.db
        settings: Settings = info.context.settings

        user = UserModel.authenticate(db=db, name=user_name, password=password)

        if not user:
            return InvalidCredentials()

        token = encode_bearer_token(
            sub=user.id,
            expiration_time=timedelta(seconds=settings.jwt_expiration_time),
            secret_key=settings.jwt_secret_key,
        )

        logger.info(logged_in_successfully(user.name))

        return UserWithToken.from_instance(
            db=db,
            instance=user,
            lock_datetime=settings.lock_datetime,
            token=token,
        )

    @strawberry.mutation
    @is_authenticated
    def modify_binary_bet_result(
        self,
        id: UUID,
        is_one_won: Optional[bool],
        info: Info,
    ) -> ModifyBinaryBetResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        bet = db.query(BinaryBetModel).filter_by(user_id=user.id, id=str(id)).first()

        if is_locked(user.name, settings.lock_datetime):
            return LockedBinaryBetError()

        if not bet:
            return BinaryBetNotFoundForUpdate()

        logger.info(modify_binary_bet_successfully(user.name, bet, is_one_won))

        bet.is_one_won = is_one_won
        db.commit()

        return BinaryBet.from_instance(db=db, instance=bet, lock_datetime=settings.lock_datetime)

    @strawberry.mutation
    @is_authenticated
    def modify_score_bet_result(
        self,
        id: UUID,
        score1: Optional[int],
        score2: Optional[int],
        info: Info,
    ) -> ModifyScoreBetResult:
        db: Session = info.context.db
        user: UserModel = info.context.user
        settings: Settings = info.context.settings

        bet = db.query(ScoreBetModel).filter_by(user_id=user.id, id=str(id)).first()

        if is_locked(user.name, settings.lock_datetime):
            return LockedScoreBetError()

        if not bet:
            return ScoreBetNotFoundForUpdate()

        if score1 is not None and score1 < 0:
            return NewScoreNegative(variable_name="$score1", score=score1)

        if score2 is not None and score2 < 0:
            return NewScoreNegative(variable_name="$score2", score=score2)

        if score1 == bet.score1 and score2 == bet.score2:
            return ScoreBet.from_instance(db=db, instance=bet, lock_datetime=settings.lock_datetime)

        db.execute(
            update(GroupPositionModel)
            .values(need_recomputation=True)
            .where(
                GroupPositionModel.team_id == bet.match.team1_id,
                GroupPositionModel.user_id == user.id,
            ),
        )
        db.execute(
            update(GroupPositionModel)
            .values(need_recomputation=True)
            .where(
                GroupPositionModel.team_id == bet.match.team2_id,
                GroupPositionModel.user_id == user.id,
            ),
        )
        logger.info(modify_score_bet_successfully(user.name, bet, score1, score2))

        bet.score1 = score1
        bet.score2 = score2
        db.commit()

        return ScoreBet.from_instance(db=db, instance=bet, lock_datetime=settings.lock_datetime)

    @strawberry.mutation
    @is_authenticated
    @is_admin_authenticated
    def modify_user_result(
        self,
        id: UUID,
        password: str,
        info: Info,
    ) -> ModifyUserResult:
        db: Session = info.context.db

        user = db.query(UserModel).filter_by(id=str(id)).first()

        if not user:
            return UserNotFound(id=id)

        user.change_password(password)
        db.commit()

        return UserWithoutSensitiveInfo.from_instance(instance=user)
