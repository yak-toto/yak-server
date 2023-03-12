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

SCHEMA_PATCH_BINARY_BET = {
    "type": "object",
    "properties": {
        "is_one_won": {
            "oneOf": [{"type": "boolean"}, {"type": "null"}],
        },
    },
    "required": ["is_one_won"],
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


SCHEMA_PUT_BINARY_BETS_BY_PHASE = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "is_one_won": {
                "oneOf": [
                    {
                        "type": "boolean",
                    },
                    {
                        "type": "null",
                    },
                ],
            },
            "index": {"type": "integer"},
            "group": {
                "type": "object",
                "properties": {"id": {"format": "uuid"}},
                "required": ["id"],
            },
            "team1": {
                "type": "object",
                "properties": {"id": {"format": "uuid"}},
                "required": ["id"],
            },
            "team2": {
                "type": "object",
                "properties": {"id": {"format": "uuid"}},
                "required": ["id"],
            },
        },
        "required": ["is_one_won", "index", "group", "team1", "team2"],
    },
}
