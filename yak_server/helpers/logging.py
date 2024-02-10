import logging.config
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from yak_server.database.models import BinaryBetModel, ScoreBetModel


def modify_score_bet_successfully(
    user_name: str,
    original_bet: "ScoreBetModel",
    new_score1: Optional[int],
    new_score2: Optional[int],
) -> str:
    return (
        f"{user_name} modify "
        f"{original_bet.match.team1.description_en}-{original_bet.match.team2.description_en} "
        f"in {original_bet.match.group.description_en} "
        f"from {original_bet.score1}-{original_bet.score2} "
        f"to {new_score1}-{new_score2}"
    )


def modify_binary_bet_successfully(
    user_name: str,
    original_bet: "BinaryBetModel",
    *,
    new_is_one_won: Optional[bool],
) -> str:
    return (
        f"{user_name} modify "
        f"{original_bet.match.team1.description_en if original_bet.match.team1 else None}"
        f"-{original_bet.match.team2.description_en if original_bet.match.team2 else None} "
        f"in {original_bet.match.group.description_en} "
        f"from {original_bet.is_one_won}-"
        f"{not original_bet.is_one_won if isinstance(original_bet.is_one_won, bool) else None} "
        f"to {new_is_one_won}-{not new_is_one_won if isinstance(new_is_one_won, bool) else None}"
    )


def signed_up_successfully(user_name: str) -> str:
    return f"{user_name} signed up successfully"


def logged_in_successfully(user_name: str) -> str:
    return f"{user_name} logged in successfully"


def modify_password_successfully(user_name: str) -> str:
    return f"admin user modify {user_name} password"


def setup_logging(*, debug: bool) -> None:
    log_dir = Path("log")
    log_dir.mkdir(exist_ok=True)

    filename = log_dir / "yak_server.log"
    log_level = "DEBUG" if debug is True else "INFO"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {},
        "formatters": {
            "simple": {"format": "%(levelname)s : %(message)s"},
            "detailed": {
                "format": "%(asctime)s - %(pathname)s:%(lineno)d - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S%z",
            },
        },
        "handlers": {
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "simple",
                "stream": "ext://sys.stderr",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": filename,
                "maxBytes": 10_485_760,  # 1 MB
                "backupCount": 10,
            },
        },
        "loggers": {"root": {"level": log_level, "handlers": ["stderr", "file"]}},
    }

    logging.config.dictConfig(logging_config)
