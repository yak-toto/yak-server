SCHEMA_POST_SCORE_BET = {
    "type": "object",
    "properties": {
        "index": {"type": "integer", "minimum": 1},
        "team1": {
            "type": "object",
            "properties": {
                "id": {"format": "uuid"},
                "score": {
                    "oneOf": [
                        {
                            "type": "integer",
                            "minimum": 0,
                        },
                        {"type": "null"},
                    ],
                },
            },
            "required": ["id"],
        },
        "team2": {
            "type": "object",
            "properties": {
                "id": {"format": "uuid"},
                "score": {
                    "oneOf": [
                        {
                            "type": "integer",
                            "minimum": 0,
                        },
                        {"type": "null"},
                    ],
                },
            },
            "required": ["id"],
        },
        "group": {
            "type": "object",
            "properties": {
                "id": {"format": "uuid"},
            },
            "required": ["id"],
        },
    },
    "required": ["team1", "team2", "group", "index"],
}

SCHEMA_PATCH_SCORE_BET = {
    "type": "object",
    "properties": {
        "team1": {
            "type": "object",
            "properties": {
                "score": {
                    "oneOf": [
                        {
                            "type": "integer",
                            "minimum": 0,
                        },
                        {"type": "null"},
                    ],
                },
            },
            "required": ["score"],
        },
        "team2": {
            "type": "object",
            "properties": {
                "score": {
                    "oneOf": [
                        {
                            "type": "integer",
                            "minimum": 0,
                        },
                        {"type": "null"},
                    ],
                },
            },
            "required": ["score"],
        },
    },
    "required": ["team1", "team2"],
}

SCHEMA_POST_BINARY_BET = {
    "type": "object",
    "properties": {
        "is_one_won": {
            "oneOf": [{"type": "boolean"}, {"type": "null"}],
        },
        "index": {"type": "integer", "minimum": 1},
        "team1": {
            "type": "object",
            "properties": {
                "id": {"format": "uuid"},
            },
            "required": ["id"],
        },
        "team2": {
            "type": "object",
            "properties": {
                "id": {"format": "uuid"},
            },
            "required": ["id"],
        },
        "group": {
            "type": "object",
            "properties": {
                "id": {"format": "uuid"},
            },
            "required": ["id"],
        },
    },
    "required": ["index", "team1", "team2", "group"],
}

SCHEMA_PATCH_BINARY_BET = {
    "type": "object",
    "properties": {
        "is_one_won": {
            "oneOf": [{"type": "boolean"}, {"type": "null"}],
        },
        "team1": {
            "type": "object",
            "properties": {
                "id": {
                    "oneOf": [
                        {"type": "string", "format": "uuid"},
                        {"type": "null"},
                    ],
                },
            },
            "required": ["id"],
        },
        "team2": {
            "type": "object",
            "properties": {"id": {"format": "uuid"}},
            "required": ["id"],
        },
    },
    "anyOf": [
        {"required": ["is_one_won"]},
        {"required": ["team1"]},
        {"required": ["team2"]},
    ],
}

SCHEMA_SIGNUP = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "password": {"type": "string"},
    },
    "required": ["name", "first_name", "last_name", "password"],
}


SCHEMA_LOGIN = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "password": {"type": "string"}},
    "required": ["name", "password"],
}


SCHEMA_PATCH_USER = {
    "type": "object",
    "properties": {"password": {"type": "string"}},
    "required": ["password"],
}
