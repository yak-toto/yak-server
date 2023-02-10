from datetime import datetime, timedelta
from itertools import chain
from typing import TYPE_CHECKING, Optional

import jwt
import strawberry
from flask import current_app

if TYPE_CHECKING:
    from strawberry.types import Info

from yak_server import db
from yak_server.database.models import BinaryBetModel, MatchModel, ScoreBetModel, UserModel

from .bearer_authenfication import AdminBearerAuthentification, bearer_authentification
from .schema import (
    BinaryBet,
    BinaryBetNotFoundForUpdate,
    InvalidCredentials,
    LockedBinaryBetError,
    LockedScoreBetError,
    LockUserResponse,
    LoginResult,
    ModifyBinaryBetResult,
    ModifyScoreBetResult,
    ScoreBet,
    ScoreBetNotFoundForUpdate,
    SignupResult,
    UserNameAlreadyExists,
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

        token = jwt.encode(
            {
                "sub": user.id,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=30),
            },
            current_app.config["SECRET_KEY"],
        )

        return UserWithToken.from_instance(instance=user, token=token)

    @strawberry.mutation
    def login_result(self, user_name: str, password: str) -> LoginResult:
        user = UserModel.authenticate(name=user_name, password=password)

        if not user:
            return InvalidCredentials()

        token = jwt.encode(
            {
                "sub": user.id,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(minutes=30),
            },
            current_app.config["SECRET_KEY"],
        )

        return UserWithToken.from_instance(instance=user, token=token)

    @strawberry.mutation
    def modify_binary_bet_result(
        self,
        id: strawberry.ID,
        is_one_won: bool,
    ) -> ModifyBinaryBetResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        bet = BinaryBetModel.query.filter_by(user_id=user.instance.id, id=id).first()

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
        id: strawberry.ID,
        score1: Optional[int],
        score2: Optional[int],
    ) -> ModifyScoreBetResult:
        user, authentification_error = bearer_authentification()

        if authentification_error:
            return authentification_error

        bet = ScoreBetModel.query.filter_by(user_id=user.instance.id, id=id).first()

        if not bet:
            return ScoreBetNotFoundForUpdate()

        if bet.locked:
            return LockedScoreBetError()

        bet.score1 = score1
        bet.score2 = score2
        db.session.commit()

        return ScoreBet.from_instance(instance=bet)

    @strawberry.mutation(permission_classes=[AdminBearerAuthentification])
    def lock_user_bet(self, user_id: str, info: "Info") -> LockUserResponse:
        score_bets = ScoreBetModel.query.filter_by(user_id=user_id)
        binary_bets = BinaryBetModel.query.filter_by(user_id=user_id)

        for bet in chain(score_bets, binary_bets):
            bet.locked = True

        db.session.commit()

        return LockUserResponse(
            score_bets=[ScoreBet.from_instance(instance=bet) for bet in score_bets],
            binary_bets=[BinaryBet.from_instance(instance=bet) for bet in binary_bets],
        )
