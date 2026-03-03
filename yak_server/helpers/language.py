from enum import Enum
from typing import Protocol


class Lang(str, Enum):
    fr = "fr"
    en = "en"


class MultiLingualDescription(Protocol):
    @property
    def description_fr(self) -> str: ...  # pragma: no cover

    @property
    def description_en(self) -> str: ...  # pragma: no cover


def get_language_description(instance: MultiLingualDescription, lang: Lang) -> str:
    if lang == Lang.fr:
        return instance.description_fr

    return instance.description_en


DEFAULT_LANGUAGE = Lang.fr
