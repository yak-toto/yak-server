import logging
from datetime import timedelta
from typing import Optional
from uuid import UUID

import strawberry
from flask import current_app
from sqlalchemy import sql, update
from strawberry.types import Info

from yak_server import db
from yak_server.database.models import (
    BinaryBetModel,
    GroupPositionModel,
    MatchModel,
    ScoreBetModel,
    UserModel,
    is_locked,
)
from yak_server.helpers.authentification import encode_bearer_token
from yak_server.helpers.group_position import create_group_position
from yak_server.helpers.logging import (
    logged_in_successfully,
    modify_binary_bet_successfully,
    modify_score_bet_successfully,
    signed_up_successfully,
)

from .bearer_authenfication import (
    is_admin_authentificated,
    is_authentificated,
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
        db.session.flush()

        # Initialize bets and integrate in db
        db.session.add_all(
            match.bet_type_from_match.value(user_id=user.id, match_id=match.id)
            for match in MatchModel.query.filter(MatchModel.bet_type_from_match is not sql.null())
        )
        db.session.flush()

        # Create group position records
        db.session.add_all(create_group_position(ScoreBetModel.query.filter_by(user_id=user.id)))
        db.session.commit()

        token = encode_bearer_token(
            sub=user.id,
            expiration_time=timedelta(seconds=current_app.config["JWT_EXPIRATION_TIME"]),
            secret_key=current_app.config["SECRET_KEY"],
        )

        logger.info(signed_up_successfully(user.name))

        return UserWithToken.from_instance(instance=user, token=token)

    @strawberry.mutation
    def login_result(self, user_name: str, password: str) -> LoginResult:
        user = UserModel.authenticate(name=user_name, password=password)

        if not user:
            return InvalidCredentials()

        token = encode_bearer_token(
            sub=user.id,
            expiration_time=timedelta(seconds=current_app.config["JWT_EXPIRATION_TIME"]),
            secret_key=current_app.config["SECRET_KEY"],
        )

        logger.info(logged_in_successfully(user.name))

        return UserWithToken.from_instance(instance=user, token=token)

    @strawberry.mutation
    @is_authentificated
    def modify_binary_bet_result(
        self,
        id: UUID,
        is_one_won: Optional[bool],
        info: Info,
    ) -> ModifyBinaryBetResult:
        bet = BinaryBetModel.query.filter_by(user_id=info.user.instance.id, id=str(id)).first()

        if is_locked(info.user.pseudo):
            return LockedBinaryBetError()

        if not bet:
            return BinaryBetNotFoundForUpdate()

        logger.info(modify_binary_bet_successfully(info.user.pseudo, bet, is_one_won))

        bet.is_one_won = is_one_won
        db.session.commit()

        return BinaryBet.from_instance(instance=bet)

    @strawberry.mutation
    @is_authentificated
    def modify_score_bet_result(
        self,
        id: UUID,
        score1: Optional[int],
        score2: Optional[int],
        info: Info,
    ) -> ModifyScoreBetResult:
        bet = ScoreBetModel.query.filter_by(user_id=info.user.instance.id, id=str(id)).first()

        if is_locked(info.user.pseudo):
            return LockedScoreBetError()

        if not bet:
            return ScoreBetNotFoundForUpdate()

        if score1 is not None and score1 < 0:
            return NewScoreNegative(variable_name="$score1", score=score1)

        if score2 is not None and score2 < 0:
            return NewScoreNegative(variable_name="$score2", score=score2)

        if score1 == bet.score1 and score2 == bet.score2:
            return ScoreBet.from_instance(instance=bet)

        db.session.execute(
            update(GroupPositionModel)
            .values(need_recomputation=True)
            .where(
                GroupPositionModel.team_id == bet.match.team1_id,
                GroupPositionModel.user_id == info.user.id,
            ),
        )
        db.session.execute(
            update(GroupPositionModel)
            .values(need_recomputation=True)
            .where(
                GroupPositionModel.team_id == bet.match.team2_id,
                GroupPositionModel.user_id == info.user.id,
            ),
        )
        logger.info(modify_score_bet_successfully(info.user.pseudo, bet, score1, score2))

        bet.score1 = score1
        bet.score2 = score2
        db.session.commit()

        return ScoreBet.from_instance(instance=bet)

    @strawberry.mutation
    @is_authentificated
    @is_admin_authentificated
    def modify_user_result(self, id: UUID, password: str, info: Info) -> ModifyUserResult:
        user = UserModel.query.filter_by(id=str(id)).first()

        if not user:
            return UserNotFound(id=id)

        user.change_password(password)
        db.session.commit()

        return UserWithoutSensitiveInfo.from_instance(instance=user)
