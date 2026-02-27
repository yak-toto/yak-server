from datetime import datetime
from pathlib import Path

import pytest

from yak_server.helpers.rules import Rules, load_rules
from yak_server.helpers.rules.compute_final_from_rank import RuleComputeFinaleFromGroupRank
from yak_server.helpers.rules.compute_points import KnockoutRoundConfig, RuleComputePoints
from yak_server.helpers.settings import Settings, get_common_settings, get_lock_datetime, get_rules

DATA_FOLDER = Path(__file__).parents[1] / "yak_server" / "data"

COMMON_SETTINGS_PARAMS = [
    pytest.param(
        "euro_2016",
        datetime.fromisoformat("2016-06-10T21:00:00+02:00"),
        "Championnat d'Europe de football 2016",
        "UEFA Euro 2016",
        id="euro_2016",
    ),
    pytest.param(
        "world_cup_2018",
        datetime.fromisoformat("2018-06-14T18:00:00+03:00"),
        "Coupe du monde de football 2018",
        "2018 FIFA World Cup",
        id="world_cup_2018",
    ),
    pytest.param(
        "euro_2020",
        datetime.fromisoformat("2021-06-11T21:00:00+02:00"),
        "Championnat d'Europe de football 2020",
        "UEFA Euro 2020",
        id="euro_2020",
    ),
    pytest.param(
        "world_cup_2022",
        datetime.fromisoformat("2022-11-20T17:00:00+01:00"),
        "Coupe du monde de football 2022",
        "2022 FIFA World Cup",
        id="world_cup_2022",
    ),
    pytest.param(
        "euro_2024",
        datetime.fromisoformat("2024-06-14T21:00:00+02:00"),
        "Championnat d'Europe de football 2024",
        "UEFA Euro 2024",
        id="euro_2024",
    ),
    pytest.param(
        "world_cup_2026",
        datetime.fromisoformat("2026-06-11T13:00:00-06:00"),
        "Coupe du monde de football 2026",
        "2026 FIFA World Cup",
        id="world_cup_2026",
    ),
]


@pytest.mark.parametrize(
    ("competition", "expected_lock_datetime", "expected_description_fr", "expected_description_en"),
    COMMON_SETTINGS_PARAMS,
)
def test_get_common_settings(
    competition: str,
    expected_lock_datetime: datetime,
    expected_description_fr: str,
    expected_description_en: str,
) -> None:
    settings = Settings(competition=competition, data_folder=DATA_FOLDER / competition)

    common_settings = get_common_settings.__wrapped__(settings)

    assert common_settings.lock_datetime == expected_lock_datetime
    assert common_settings.competition.description_fr == expected_description_fr
    assert common_settings.competition.description_en == expected_description_en


LOCK_DATETIME_PARAMS = [(p.values[0], p.values[1]) for p in COMMON_SETTINGS_PARAMS]


@pytest.mark.parametrize(("competition", "expected_lock_datetime"), LOCK_DATETIME_PARAMS)
def test_get_lock_datetime(
    competition: str,
    expected_lock_datetime: datetime,
) -> None:
    settings = Settings(competition=competition, data_folder=DATA_FOLDER / competition)
    common_settings = get_common_settings.__wrapped__(settings)

    lock_datetime = get_lock_datetime.__wrapped__(common_settings)

    assert lock_datetime.tzinfo is not None
    assert lock_datetime == expected_lock_datetime


RULES_PARAMS = [
    pytest.param(
        "world_cup_2022",
        RuleComputeFinaleFromGroupRank(
            to_group="8",
            from_phase="GROUP",
            versus=[
                {"team1": {"rank": 1, "group": "A"}, "team2": {"rank": 2, "group": "B"}},
                {"team1": {"rank": 1, "group": "C"}, "team2": {"rank": 2, "group": "D"}},
                {"team1": {"rank": 1, "group": "E"}, "team2": {"rank": 2, "group": "F"}},
                {"team1": {"rank": 1, "group": "G"}, "team2": {"rank": 2, "group": "H"}},
                {"team1": {"rank": 1, "group": "B"}, "team2": {"rank": 2, "group": "A"}},
                {"team1": {"rank": 1, "group": "D"}, "team2": {"rank": 2, "group": "C"}},
                {"team1": {"rank": 1, "group": "F"}, "team2": {"rank": 2, "group": "E"}},
                {"team1": {"rank": 1, "group": "H"}, "team2": {"rank": 2, "group": "G"}},
            ],
        ),
        RuleComputePoints(
            base_correct_result=1,
            multiplying_factor_correct_result=2,
            base_correct_score=3,
            multiplying_factor_correct_score=7,
            team_qualified=10,
            first_team_qualified=20,
            knockout_rounds=[
                KnockoutRoundConfig(group_code="4", points_per_team=30),
                KnockoutRoundConfig(group_code="2", points_per_team=60),
                KnockoutRoundConfig(group_code="1", points_per_team=120),
            ],
            winner_group_code="1",
            winner_points=200,
        ),
        id="world_cup_2022",
    ),
    pytest.param(
        "world_cup_2026",
        None,  # Too large to inline; structural checks done separately
        RuleComputePoints(
            base_correct_result=1,
            multiplying_factor_correct_result=2,
            base_correct_score=3,
            multiplying_factor_correct_score=7,
            team_qualified=10,
            first_team_qualified=20,
            knockout_rounds=[
                KnockoutRoundConfig(group_code="8", points_per_team=15),
                KnockoutRoundConfig(group_code="4", points_per_team=30),
                KnockoutRoundConfig(group_code="2", points_per_team=60),
                KnockoutRoundConfig(group_code="1", points_per_team=120),
            ],
            winner_group_code="1",
            winner_points=200,
        ),
        id="world_cup_2026",
    ),
]


@pytest.mark.parametrize(
    ("competition", "expected_compute_finale", "expected_compute_points"),
    RULES_PARAMS,
)
def test_load_rules(
    competition: str,
    expected_compute_finale: RuleComputeFinaleFromGroupRank | None,
    expected_compute_points: RuleComputePoints,
) -> None:
    data_folder = DATA_FOLDER / competition

    rules = load_rules(data_folder)

    assert rules.compute_finale_phase_from_group_rank is not None
    assert rules.compute_points is not None
    assert rules.compute_points == expected_compute_points

    if expected_compute_finale is not None:
        assert rules.compute_finale_phase_from_group_rank == expected_compute_finale


@pytest.mark.parametrize(
    ("competition", "expected_compute_finale", "expected_compute_points"),
    RULES_PARAMS,
)
def test_get_rules(
    competition: str,
    expected_compute_finale: RuleComputeFinaleFromGroupRank | None,
    expected_compute_points: RuleComputePoints,
) -> None:
    settings = Settings(competition=competition, data_folder=DATA_FOLDER / competition)

    rules = get_rules.__wrapped__(settings)

    assert rules.compute_finale_phase_from_group_rank is not None
    assert rules.compute_points is not None
    assert rules.compute_points == expected_compute_points

    if expected_compute_finale is not None:
        assert rules.compute_finale_phase_from_group_rank == expected_compute_finale


@pytest.mark.parametrize(
    "competition",
    ["euro_2016", "world_cup_2018", "euro_2020", "euro_2024"],
)
def test_load_rules_no_rules_configured(competition: str) -> None:
    rules = load_rules(DATA_FOLDER / competition)

    assert rules == Rules()


def test_load_rules_world_cup_2026_compute_finale_structure() -> None:
    rules = load_rules(DATA_FOLDER / "world_cup_2026")

    config = rules.compute_finale_phase_from_group_rank
    assert config is not None
    assert config.to_group == "16"
    assert config.from_phase == "GROUP"
    assert config.third_place_lookup is not None
    assert config.third_place_matchup is not None
    # 16 matches in the Round of 32 (48 teams, 8 fixed + 8 dynamic third-place slots)
    assert len(config.versus) == 16
    dynamic_slots = [
        v
        for v in config.versus
        if (v.team1.rank == 3 and not v.team1.group) or (v.team2.rank == 3 and not v.team2.group)
    ]
    assert len(dynamic_slots) == 8
