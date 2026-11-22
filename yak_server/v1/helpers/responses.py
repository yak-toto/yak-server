from typing import Any

from fastapi import status

from yak_server.v1.models.generic import ErrorOut, ValidationErrorOut


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    # Document each given status code as returning an ``ErrorOut`` body.
    return {status_code: {"model": ErrorOut} for status_code in status_codes}


VALIDATION_ERROR_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut},
}
