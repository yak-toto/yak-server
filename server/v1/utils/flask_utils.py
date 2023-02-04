import re

from flask import jsonify


def success_response(status_code, result):
    return jsonify({"ok": True, "result": result}), status_code


def is_uuid4(uuid):
    regex = re.compile(
        r"^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z",
    )
    match = regex.match(uuid)
    return bool(match)


def is_iso_3166_1_alpha_2_code(code):
    regex = re.compile(r"^([A-Z]{2}|[A-Z]{2}-[A-Z]{3})\Z")
    match = regex.match(code)
    return bool(match)
