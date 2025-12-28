from enum import Enum
from typing import Protocol


class Lang(str, Enum):
    fr = "fr"
    en = "en"


class MultiLingualDescription(Protocol):
    description_fr: str
    description_en: str


def get_language_description(instance: MultiLingualDescription, lang: Lang) -> str:
    if lang == Lang.fr:
        return instance.description_fr

    return instance.description_en


DEFAULT_LANGUAGE = Lang.fr
