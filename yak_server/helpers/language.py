from enum import Enum
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from yak_server.database.models import GroupModel, PhaseModel, TeamModel


class Lang(str, Enum):
    fr = "fr"
    en = "en"


def get_language_description(
    instance: Union["GroupModel", "PhaseModel", "TeamModel"],
    lang: Lang,
) -> str:
    if lang == Lang.fr:
        return instance.description_fr

    return instance.description_en


DEFAULT_LANGUAGE = Lang.fr
