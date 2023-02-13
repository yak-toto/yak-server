import uuid
from datetime import timedelta
from itertools import chain
from typing import Optional

import strawberry
from flask import current_app

from yak_server import db
from yak_server.database.models import BinaryBetModel, MatchModel, ScoreBetModel, UserModel

from .bearer_authenfication import (
    admin_bearer_authentification,
    bearer_authentification,
    encode_bearer_token,
)
from .result import (
    BinaryBetNotFoundForUpdate,
    InvalidCredentials,
    LockedBinaryBetError,
    LockedScoreBetError,
    LockUserResult,
    LoginResult,
    ModifyBinaryBetResult,
    ModifyScoreBetResult,
    NewScoreNegative,
    ScoreBetNotFoundForUpdate,
    SignupResult,
    UserNameAlreadyExists,
    UserNotFound,
)
from .schema import (
    BinaryBet,
    ScoreBet,
    User,
    UserWithToken,
)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def signup_result(
        self,
        user_name: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> SignupResult:
        # Check existing user in db
        existing_user = UserModel.query.filter_by(name=user_name).first()
        if existing_user:
            return UserNameAlreadyExists(user_name=user_name)

        # Initialize user and integrate in db
        user = UserModel(
            name=user_name,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        db.session.add(user)
        db.session.commit()

        # Initialize bets and integrate in db
        db.session.add_all(
            ScoreBetModel(user_id=user.id, match_id=match.id) for match in MatchModel.query.all()
        )
        db.session.commit()

        token = encode_bearer_token(
            sub=user.id,
            expiration_time=timedelta(minutes=30),
            secret_key=current_app.config["SECRET_KEY"],
        )

        return UserWithToken.from_instance(instance=user, token=token)

    @strawberry.mutation
    def login_result(self, user_name: str, password: str) -> LoginResult:
        user = UserModel.authenticate(name=user_name, password=password)

        if not user:
            return InvalidCredentials()

        token = encode_bearer_token(
            sub=user.id,
            expiration_time=timedelta(minutes=30),
            secret_key=current_app.config["SECRET_KEY"],
        )

        return UserWithToken.from_instance(instance=user, token=token)

    @strawberry.mutation
    def modify_binary_bet_result(
        self,
        id: uuid.UUID,
        is_one_won: Optional[bool],
    ) -> ModifyBinaryBetResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        bet = BinaryBetModel.query.filter_by(user_id=user.instance.id, id=str(id)).first()

        if not bet:
            return BinaryBetNotFoundForUpdate()

        if bet.locked:
            return LockedBinaryBetError()

        bet.is_one_won = is_one_won
        db.session.commit()

        return BinaryBet.from_instance(instance=bet)

    @strawberry.mutation
    def modify_score_bet_result(
        self,
        id: uuid.UUID,
        score1: Optional[int],
        score2: Optional[int],
    ) -> ModifyScoreBetResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        bet = ScoreBetModel.query.filter_by(user_id=user.instance.id, id=str(id)).first()

        if not bet:
            return ScoreBetNotFoundForUpdate()

        if bet.locked:
            return LockedScoreBetError()

        if score1 is not None and score1 < 0:
            return NewScoreNegative(variable_name="$score1", score=score1)

        if score2 is not None and score2 < 0:
            return NewScoreNegative(variable_name="$score2", score=score2)

        bet.score1 = score1
        bet.score2 = score2
        db.session.commit()

        return ScoreBet.from_instance(instance=bet)

    @strawberry.mutation
    def modify_user_lock_result(self, user_id: uuid.UUID, lock: bool) -> LockUserResult:
        _, authentification_error = admin_bearer_authentification()

        if authentification_error:
            return authentification_error

        user_to_be_locked = UserModel.query.filter_by(id=str(user_id)).first()

        if not user_to_be_locked:
            return UserNotFound(user_id=user_id)

        for bet in chain(user_to_be_locked.score_bets, user_to_be_locked.binary_bets):
            bet.locked = lock

        db.session.commit()

        return User.from_instance(instance=user_to_be_locked)
