from functools import wraps

from flask import request
from jsonschema import Draft202012Validator, ValidationError, validate

from .errors import RequestValidationError


def validate_body(schema):  # noqa: ANN201
    def decorator(f):
        @wraps(f)
        def _verify(*args, **kwargs):
            try:
                validate(
                    instance=request.get_json(),
                    schema=schema,
                    format_checker=Draft202012Validator.FORMAT_CHECKER,
                )
            except ValidationError as validation_error:
                raise RequestValidationError(
                    schema=validation_error.schema,
                    description=validation_error.message,
                    path=list(validation_error.absolute_path),
                ) from validation_error

            return f(*args, **kwargs)

        return _verify

    return decorator
