import secrets
import string
from dataclasses import dataclass
from http import HTTPStatus
from typing import List, Optional, Tuple

from fastapi.testclient import TestClient


def get_random_string(length: int) -> str:
    return "".join(secrets.choice(string.ascii_letters) for _ in range(length))


@dataclass
class UserData:
    first_name: str
    last_name: str
    name: str
    scores: List[Optional[Tuple[Optional[int], Optional[int]]]]
    token: Optional[str] = None


def patch_score_bets(
    client: TestClient,
    token: str,
    new_scores: List[Optional[Tuple[Optional[int], Optional[int]]]],
) -> None:
    response_get_all_bets = client.get("/api/v1/bets", headers={"Authorization": f"Bearer {token}"})

    assert response_get_all_bets.status_code == HTTPStatus.OK

    for bet, new_score in zip(response_get_all_bets.json()["result"]["score_bets"], new_scores):
        if new_score is not None:
            response_patch_score_bet = client.patch(
                f"/api/v1/score_bets/{bet['id']}",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "team1": {"score": new_score[0]},
                    "team2": {"score": new_score[1]},
                },
            )

            assert response_patch_score_bet.status_code == HTTPStatus.OK
