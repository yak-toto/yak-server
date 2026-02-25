from http import HTTPStatus
from typing import TYPE_CHECKING

from testing.util import get_random_string
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    PhaseModel,
    Role,
    TeamModel,
    UserModel,
)
from yak_server.database.session import build_local_session_maker
from yak_server.helpers.rules.compute_final_from_rank import (
    RuleComputeFinaleFromGroupRank,
    Team,
    Versus,
    _resolve_third_place_assignment,
    compute_finale_phase_from_group_rank,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlalchemy.orm import Session

# A generic lookup / matchup used across multiple tests.
# Qualified key "EFGHIJKL" -> first 8 positions map to match indices via _MATCHUP.
_LOOKUP: dict[str, list[str]] = {
    "EFGHIJKL": ["3E", "3J", "3I", "3F", "3H", "3G", "3L", "3K"],
}
_MATCHUP: list[int] = [11, 15, 7, 1, 8, 2, 16, 12]


def _full_group_result(third_place_pts: int) -> list[GroupPositionModel]:
    """Return a 4-team group where all teams have played 3 games.

    The 3rd-place team has the given point total (won * 3) and 1 goal scored.

    Returns:
        Sorted list of GroupPositionModel from 1st to 4th place.
    """
    third_won = third_place_pts // 3
    return [
        GroupPositionModel(won=3, drawn=0, lost=0, goals_for=0, goals_against=0),  # 1st - 9 pts
        GroupPositionModel(won=2, drawn=0, lost=1, goals_for=6, goals_against=3),  # 2nd - 6 pts
        GroupPositionModel(  # 3rd
            won=third_won, drawn=0, lost=3 - third_won, goals_for=1, goals_against=5
        ),
        GroupPositionModel(won=0, drawn=0, lost=3, goals_for=0, goals_against=9),  # 4th - 0 pts
    ]


# ── _resolve_third_place_assignment tests ──────────────────────────────────────


def test_returns_empty_when_groups_incomplete() -> None:
    """Returns {} as long as at least one group is not fully played."""
    groups_result = {code: _full_group_result(6) for code in "ABCDEFGHIJKL"}
    # Sabotage group A: one team has only played 2 games instead of 3.
    groups_result["A"][0] = GroupPositionModel(
        won=2, drawn=0, lost=0, goals_for=6, goals_against=0, team=TeamModel(id="t0")
    )

    assert _resolve_third_place_assignment(groups_result, _LOOKUP, _MATCHUP) == {}


def test_basic_assignment() -> None:
    """Best 8 of 12 third-place teams are selected; lookup + matchup produce correct dict."""
    # E-L have 6 pts at 3rd place, A-D have 3 pts -> qualified key = "EFGHIJKL"
    groups_result = {
        **{code: _full_group_result(3) for code in "ABCD"},
        **{code: _full_group_result(6) for code in "EFGHIJKL"},
    }

    result = _resolve_third_place_assignment(groups_result, _LOOKUP, _MATCHUP)

    # "EFGHIJKL" -> ["3E","3J","3I","3F","3H","3G","3L","3K"] zipped with [11,15,7,1,8,2,16,12]
    assert result == {
        11: "E",
        15: "J",
        7: "I",
        1: "F",
        8: "H",
        2: "G",
        16: "L",
        12: "K",
    }


def test_tiebreaker_goals_difference() -> None:
    """When points are equal, goals_difference breaks the tie."""

    # All 12 groups have equal 3rd-place points; groups E-L have better goals_difference (+1 vs -4).
    def _group_with_gd(goals_for: int, goals_against: int) -> list[GroupPositionModel]:
        return [
            GroupPositionModel(
                won=3, drawn=0, lost=0, goals_for=9, goals_against=0, team=TeamModel(id="1")
            ),
            GroupPositionModel(
                won=2, drawn=0, lost=1, goals_for=6, goals_against=3, team=TeamModel(id="2")
            ),
            GroupPositionModel(  # 3rd - 3 pts
                won=1,
                drawn=0,
                lost=2,
                goals_for=goals_for,
                goals_against=goals_against,
                team=TeamModel(id="3"),
            ),
            GroupPositionModel(
                won=0, drawn=0, lost=3, goals_for=0, goals_against=9, team=TeamModel(id="4")
            ),
        ]

    groups_result = {
        **{c: _group_with_gd(1, 5) for c in "ABCD"},  # GD = -4
        **{c: _group_with_gd(2, 1) for c in "EFGHIJKL"},  # GD = +1
    }

    result = _resolve_third_place_assignment(groups_result, _LOOKUP, _MATCHUP)

    assert set(result.values()) == set("EFGHIJKL")


def test_tiebreaker_goals_for() -> None:
    """When points and goals_difference are equal, goals_for breaks the tie."""

    def _group_with_gf(goals_for: int) -> list[GroupPositionModel]:
        return [
            GroupPositionModel(
                won=3, drawn=0, lost=0, goals_for=9, goals_against=0, team=TeamModel(id="1")
            ),
            GroupPositionModel(
                won=2, drawn=0, lost=1, goals_for=6, goals_against=3, team=TeamModel(id="2")
            ),
            GroupPositionModel(  # 3pts, GD=+1 always
                won=1,
                drawn=0,
                lost=2,
                goals_for=goals_for,
                goals_against=goals_for - 1,
                team=TeamModel(id="3"),
            ),
            GroupPositionModel(
                won=0, drawn=0, lost=3, goals_for=0, goals_against=9, team=TeamModel(id="4")
            ),
        ]

    groups_result = {
        **{c: _group_with_gf(2) for c in "ABCD"},  # goals_for = 2
        **{c: _group_with_gf(5) for c in "EFGHIJKL"},  # goals_for = 5
    }

    result = _resolve_third_place_assignment(groups_result, _LOOKUP, _MATCHUP)

    assert set(result.values()) == set("EFGHIJKL")


# ── compute_finale_phase_from_group_rank tests ────────────────────────────────


def _populate_group_stage(
    db: "Session",
    group_pts: dict[str, int],
) -> tuple[UserModel, dict[str, list[TeamModel]]]:
    """Insert a GROUP phase with groups, teams, and positions into the database.

    Each group gets 4 teams. The 3rd-place team's points are controlled by the
    value in group_pts. Teams are inserted in rank order (1st to 4th).

    Returns:
        The created user and a {group_code: [TeamModel, ...]} dict where
        each list is ordered from 1st to 4th place.
    """
    group_phase = PhaseModel(
        code="GROUP", description_fr="Groupes", description_en="Groups", index=1
    )
    db.add(group_phase)
    user = UserModel(
        name="user",
        first_name="u",
        last_name="u",
        password=get_random_string(15),
        role=Role.USER,
    )
    db.add(user)
    db.flush()

    teams_by_group: dict[str, list[TeamModel]] = {}
    for group_idx, (code, pts) in enumerate(group_pts.items(), 1):
        third_won = pts // 3
        group = GroupModel(
            code=code,
            description_fr=f"Groupe {code}",
            description_en=f"Group {code}",
            index=group_idx,
            phase_id=group_phase.id,
        )
        db.add(group)
        db.flush()

        # (won, drawn, lost, goals_for, goals_against) for each rank
        positions = [
            (3, 0, 0, 9, 0),  # 1st - 9 pts
            (2, 0, 1, 6, 3),  # 2nd - 6 pts
            (third_won, 0, 3 - third_won, 1, 5),  # 3rd
            (0, 0, 3, 0, 9),  # 4th - 0 pts
        ]
        teams: list[TeamModel] = []
        for pos_idx, (won, drawn, lost, gf, ga) in enumerate(positions, 1):
            team = TeamModel(
                code=f"{code}{pos_idx}",
                description_fr=f"Team {code}{pos_idx}",
                description_en=f"Team {code}{pos_idx}",
                flag_url="",
                internal_flag_url="",
            )
            db.add(team)
            db.flush()
            db.add(
                GroupPositionModel(
                    won=won,
                    drawn=drawn,
                    lost=lost,
                    goals_for=gf,
                    goals_against=ga,
                    user_id=user.id,
                    team_id=team.id,
                    group_id=group.id,
                )
            )
            teams.append(team)
        db.flush()
        teams_by_group[code] = teams

    return user, teams_by_group


def test_group_not_found_returns_404(engine_for_test: "Engine") -> None:
    """Returns 404 when to_group does not exist in the database."""
    local_session_maker = build_local_session_maker(engine_for_test)
    user = UserModel(
        name="user",
        first_name="u",
        last_name="u",
        password=get_random_string(15),
        role=Role.USER,
    )
    rule = RuleComputeFinaleFromGroupRank(to_group="99", from_phase="GROUP", versus=[])

    with local_session_maker() as db:
        status_code, _ = compute_finale_phase_from_group_rank(db, user, rule)

    assert status_code == HTTPStatus.NOT_FOUND


def test_static_slot_assigns_correct_team(engine_for_test_with_delete: "Engine") -> None:
    """Static slots (no third_place_lookup) resolve rank directly from the group."""
    local_session_maker = build_local_session_maker(engine_for_test_with_delete)

    with local_session_maker() as db:
        user, teams_by_group = _populate_group_stage(db, {"A": 6, "B": 6})

        finale_phase = PhaseModel(
            code="FINALE", description_fr="Finale", description_en="Finale", index=2
        )
        db.add(finale_phase)
        db.flush()

        finale_group = GroupModel(
            code="8",
            description_fr="Groupe 8",
            description_en="Group 8",
            index=3,
            phase_id=finale_phase.id,
        )
        db.add(finale_group)
        db.flush()

        match = MatchModel(group_id=finale_group.id, index=1, user_id=user.id)
        db.add(match)
        db.flush()
        db.add(BinaryBetModel(match_id=match.id))
        db.flush()

        team_a1_id = teams_by_group["A"][0].id
        team_b2_id = teams_by_group["B"][1].id
        match_id = match.id

        rule = RuleComputeFinaleFromGroupRank(
            to_group="8",
            from_phase="GROUP",
            versus=[Versus(team1=Team(rank=1, group="A"), team2=Team(rank=2, group="B"))],
        )
        compute_finale_phase_from_group_rank(db, user, rule)

        updated_match = db.query(MatchModel).filter_by(id=match_id).first()
        assert updated_match is not None
        assert updated_match.team1_id == team_a1_id
        assert updated_match.team2_id == team_b2_id


def test_static_slot_skipped_when_incomplete(engine_for_test_with_delete: "Engine") -> None:
    """Static match is not updated when either group has not finished playing."""
    local_session_maker = build_local_session_maker(engine_for_test_with_delete)

    with local_session_maker() as db:
        user, _ = _populate_group_stage(db, {"A": 6, "B": 6})

        # Make group B's top position incomplete (won=2, lost=0 -> played=2 instead of 3).
        group_b = db.query(GroupModel).filter_by(code="B").first()
        assert group_b is not None
        top_pos = (
            db
            .query(GroupPositionModel)
            .filter_by(group_id=group_b.id, user_id=user.id, won=3)
            .first()
        )
        assert top_pos is not None
        top_pos.won = 2

        finale_phase = PhaseModel(
            code="FINALE", description_fr="Finale", description_en="Finale", index=2
        )
        db.add(finale_phase)
        db.flush()

        finale_group = GroupModel(
            code="8",
            description_fr="Groupe 8",
            description_en="Group 8",
            index=3,
            phase_id=finale_phase.id,
        )
        db.add(finale_group)
        db.flush()

        match = MatchModel(group_id=finale_group.id, index=1, user_id=user.id)
        db.add(match)
        db.flush()
        db.add(BinaryBetModel(match_id=match.id))
        db.flush()

        match_id = match.id

        rule = RuleComputeFinaleFromGroupRank(
            to_group="8",
            from_phase="GROUP",
            versus=[Versus(team1=Team(rank=1, group="A"), team2=Team(rank=2, group="B"))],
        )
        compute_finale_phase_from_group_rank(db, user, rule)

        updated_match = db.query(MatchModel).filter_by(id=match_id).first()
        assert updated_match is not None
        assert updated_match.team1_id is None
        assert updated_match.team2_id is None


def test_dynamic_slot_assigns_correct_team(engine_for_test_with_delete: "Engine") -> None:
    """Dynamic rank-3 slot resolves via lookup+matchup and updates the correct match.

    E-L qualify as 3rd place (6 pts > A-D's 3 pts) -> key "EFGHIJKL".
    matchup[3]=1 and lookup[3]="3F" -> match index 1 gets group F's 3rd-place team.
    """
    local_session_maker = build_local_session_maker(engine_for_test_with_delete)

    with local_session_maker() as db:
        user, teams_by_group = _populate_group_stage(
            db,
            {**dict.fromkeys("ABCD", 3), **dict.fromkeys("EFGHIJKL", 6)},
        )

        finale_phase = PhaseModel(
            code="FINALE", description_fr="Finale", description_en="Finale", index=2
        )
        db.add(finale_phase)
        db.flush()

        finale_group = GroupModel(
            code="16",
            description_fr="Groupe 16",
            description_en="Group 16",
            index=13,
            phase_id=finale_phase.id,
        )
        db.add(finale_group)
        db.flush()

        match = MatchModel(group_id=finale_group.id, index=1, user_id=user.id)
        db.add(match)
        db.flush()
        db.add(BinaryBetModel(match_id=match.id))
        db.flush()

        team_e1_id = teams_by_group["E"][0].id  # 1st of group E
        team_f3_id = teams_by_group["F"][2].id  # 3rd of group F
        match_id = match.id

        rule = RuleComputeFinaleFromGroupRank(
            to_group="16",
            from_phase="GROUP",
            versus=[Versus(team1=Team(rank=1, group="E"), team2=Team(rank=3, group=""))],
            third_place_lookup={"EFGHIJKL": ["3E", "3J", "3I", "3F", "3H", "3G", "3L", "3K"]},
            third_place_matchup=[11, 15, 7, 1, 8, 2, 16, 12],
        )
        compute_finale_phase_from_group_rank(db, user, rule)

        updated_match = db.query(MatchModel).filter_by(id=match_id).first()
        assert updated_match is not None
        assert updated_match.team1_id == team_e1_id
        assert updated_match.team2_id == team_f3_id


def test_dynamic_slot_skipped_when_groups_incomplete(
    engine_for_test_with_delete: "Engine",
) -> None:
    """Dynamic slot is not updated when any group has not finished playing."""
    local_session_maker = build_local_session_maker(engine_for_test_with_delete)

    with local_session_maker() as db:
        user, _ = _populate_group_stage(
            db,
            {**dict.fromkeys("ABCD", 3), **dict.fromkeys("EFGHIJKL", 6)},
        )

        # Make group A's top position incomplete (won=2, lost=0 -> played=2 instead of 3).
        group_a = db.query(GroupModel).filter_by(code="A").first()
        assert group_a is not None
        top_pos = (
            db
            .query(GroupPositionModel)
            .filter_by(group_id=group_a.id, user_id=user.id, won=3)
            .first()
        )
        assert top_pos is not None
        top_pos.won = 2

        finale_phase = PhaseModel(
            code="FINALE", description_fr="Finale", description_en="Finale", index=2
        )
        db.add(finale_phase)
        db.flush()

        finale_group = GroupModel(
            code="16",
            description_fr="Groupe 16",
            description_en="Group 16",
            index=13,
            phase_id=finale_phase.id,
        )
        db.add(finale_group)
        db.flush()

        match = MatchModel(group_id=finale_group.id, index=1, user_id=user.id)
        db.add(match)
        db.flush()
        db.add(BinaryBetModel(match_id=match.id))
        db.flush()

        match_id = match.id

        rule = RuleComputeFinaleFromGroupRank(
            to_group="16",
            from_phase="GROUP",
            versus=[Versus(team1=Team(rank=1, group="E"), team2=Team(rank=3, group=""))],
            third_place_lookup={"EFGHIJKL": ["3E", "3J", "3I", "3F", "3H", "3G", "3L", "3K"]},
            third_place_matchup=[11, 15, 7, 1, 8, 2, 16, 12],
        )
        compute_finale_phase_from_group_rank(db, user, rule)

        updated_match = db.query(MatchModel).filter_by(id=match_id).first()
        assert updated_match is not None
        assert updated_match.team1_id is None
        assert updated_match.team2_id is None
