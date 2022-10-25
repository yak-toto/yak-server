from .constants import BINARY
from .constants import SCORE

invalid_credentials = (401, "Invalid credentials")
invalid_name = (401, "Name already exists")
match_not_found = (404, "Match not found")
wrong_inputs = (401, "Wrong inputs")
missing_id = (401, "Missing id(s) in one bet")
duplicated_ids = (401, "Duplicated ids in request")
unauthorized_access_to_admin_api = (401, "Unauthorized access to admin API")
invalid_token = (401, "Invalid token. Registeration and / or authentication required")
expired_token = (401, "Expired token. Reauthentication required.")
invalid_team_id = (
    400,
    "Invalid team id. Retry with a uuid or ISO 3166-1 alpha-2 code.",
)
team_not_found = (404, "No team found for the requested id.")
locked_bets = (401, "Cannot modify bets because locked date is exceeded.")
invalid_bet_type = (
    401,
    f"Invalid bet type. The available bet types are : {SCORE, BINARY}.",
)
