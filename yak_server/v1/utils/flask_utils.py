import re
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union

from flask import jsonify

if TYPE_CHECKING:
    from flask import Response


def success_response(
    status_code: int,
    result: Union[None, List[Any], Dict[str, Any]],
) -> Tuple["Response", int]:
    return jsonify({"ok": True, "result": result}), status_code


def is_uuid4(uuid: str) -> bool:
    regex = re.compile(
        r"^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z",
    )
    match = regex.match(uuid)
    return bool(match)


def is_iso_3166_1_alpha_2_code(code: str) -> bool:
    regex = re.compile(r"^([A-Z]{2}|[A-Z]{2}-[A-Z]{3})\Z")
    match = regex.match(code)
    return bool(match)
