from flask import jsonify


def success_response(status_code, result):
    return jsonify(dict(ok=True, result=result)), status_code


def failed_response(error_code, description):
    return (
        jsonify(dict(ok=False, error_code=error_code, description=description)),
        error_code,
    )
