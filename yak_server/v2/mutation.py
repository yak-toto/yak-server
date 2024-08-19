import logging
from typing import Optional
from uuid import UUID

import pendulum
import strawberry
from sqlalchemy import and_
from strawberry.types import Info

from yak_server.database.models import (
    BinaryBetModel,
    MatchModel,
    ScoreBetModel,
    UserModel,
)
from yak_server.helpers.authentication import (
    NameAlreadyExistsError,
    encode_bearer_token,
    signup_user,
)
from yak_server.helpers.bet_locking import is_locked
from yak_server.helpers.group_position import set_recomputation_flag
from yak_server.helpers.logging_helpers import (
    logged_in_successfully,
    modify_binary_bet_successfully,
    modify_score_bet_successfully,
    signed_up_successfully,
)
from yak_server.helpers.password_validator import PasswordRequirementsError

from .bearer_authentication import (
    is_admin_authenticated,
    is_authenticated,
)
from .context import YakContext
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
    UnsatisfiedPasswordRequirements,
    UserNameAlreadyExists,
    UserNotFound,
    UserWithoutSensitiveInfo,
)
from .schema import (
    BinaryBet,
    ScoreBet,
    UserWithToken,
)

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
        info: Info[YakContext, None],
    ) -> SignupResult:
        db = info.context.db
        settings = info.context.settings

        try:
            user = signup_user(
                db, name=user_name, first_name=first_name, last_name=last_name, password=password
            )
        except PasswordRequirementsError as password_requirements_error:
            return UnsatisfiedPasswordRequirements(message=str(password_requirements_error))
        except NameAlreadyExistsError:
            return UserNameAlreadyExists(user_name=user_name)

        logger.info(signed_up_successfully(user.name))

        return UserWithToken.from_instance(
            user,
            db=db,
            lock_datetime=settings.lock_datetime,
            token=encode_bearer_token(
                sub=user.id,
                expiration_time=pendulum.duration(seconds=settings.jwt_expiration_time),
                secret_key=settings.jwt_secret_key,
            ),
        )

    @strawberry.mutation
    def login_result(
        self,
        user_name: str,
        password: str,
        info: Info[YakContext, None],
    ) -> LoginResult:
        db = info.context.db
        settings = info.context.settings

        user = UserModel.authenticate(db=db, name=user_name, password=password)

        if not user:
            return InvalidCredentials()

        token = encode_bearer_token(
            sub=user.id,
            expiration_time=pendulum.duration(seconds=settings.jwt_expiration_time),
            secret_key=settings.jwt_secret_key,
        )

        logger.info(logged_in_successfully(user.name))

        return UserWithToken.from_instance(
            user,
            db=db,
            lock_datetime=settings.lock_datetime,
            token=token,
        )

    @strawberry.mutation
    @is_authenticated
    def modify_binary_bet_result(
        self,
        id: UUID,
        is_one_won: Optional[bool],  # noqa: FBT001
        info: Info[YakContext, None],
    ) -> ModifyBinaryBetResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        bet = (
            db.query(BinaryBetModel)
            .join(BinaryBetModel.match)
            .filter(and_(MatchModel.user_id == user.id, BinaryBetModel.id == id))
            .first()
        )

        if is_locked(user.name, settings.lock_datetime):
            return LockedBinaryBetError()

        if not bet:
            return BinaryBetNotFoundForUpdate()

        logger.info(modify_binary_bet_successfully(user.name, bet, new_is_one_won=is_one_won))

        bet.is_one_won = is_one_won
        db.commit()

        return BinaryBet.from_instance(bet, db=db, lock_datetime=settings.lock_datetime)

    @strawberry.mutation
    @is_authenticated
    def modify_score_bet_result(
        self,
        id: UUID,
        score1: Optional[int],
        score2: Optional[int],
        info: Info[YakContext, None],
    ) -> ModifyScoreBetResult:
        db = info.context.db
        user = info.context.user
        settings = info.context.settings

        bet = (
            db.query(ScoreBetModel)
            .join(ScoreBetModel.match)
            .filter(and_(MatchModel.user_id == user.id, ScoreBetModel.id == id))
            .first()
        )

        if is_locked(user.name, settings.lock_datetime):
            return LockedScoreBetError()

        if not bet:
            return ScoreBetNotFoundForUpdate()

        if score1 is not None and score1 < 0:
            return NewScoreNegative(variable_name="$score1", score=score1)

        if score2 is not None and score2 < 0:
            return NewScoreNegative(variable_name="$score2", score=score2)

        if score1 == bet.score1 and score2 == bet.score2:
            return ScoreBet.from_instance(bet, db=db, lock_datetime=settings.lock_datetime)

        set_recomputation_flag(db, bet.match.team1_id, user.id)
        set_recomputation_flag(db, bet.match.team2_id, user.id)

        logger.info(modify_score_bet_successfully(user.name, bet, score1, score2))

        bet.score1 = score1
        bet.score2 = score2
        db.commit()

        return ScoreBet.from_instance(bet, db=db, lock_datetime=settings.lock_datetime)

    @strawberry.mutation
    @is_authenticated
    @is_admin_authenticated
    def modify_user_result(
        self,
        id: UUID,
        password: str,
        info: Info[YakContext, None],
    ) -> ModifyUserResult:
        db = info.context.db

        user = db.query(UserModel).filter_by(id=id).first()

        if not user:
            return UserNotFound(id=id)

        user.change_password(password)
        db.commit()

        return UserWithoutSensitiveInfo.from_instance(user)
