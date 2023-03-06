def modify_score_bet_successfully(user_name, original_bet, new_score1, new_score2) -> str:
    return (
        f"{user_name} modify "
        f"{original_bet.match.team1.description}-{original_bet.match.team2.description} "
        f"in {original_bet.match.group.description} "
        f"from {original_bet.score1}-{original_bet.score2} "
        f"to {new_score1}-{new_score2}"
    )


def modify_binary_bet_successfully(user_name, original_bet, new_is_one_won) -> str:
    return (
        f"{user_name} modify "
        f"{original_bet.match.team1.description}-{original_bet.match.team2.description} "
        f"in {original_bet.match.group.description} "
        f"from {original_bet.is_one_won}-"
        f"{not original_bet.is_one_won if isinstance(original_bet.is_one_won, bool) else None} "
        f"to {new_is_one_won}-{not new_is_one_won if isinstance(new_is_one_won, bool) else None}"
    )


def signed_up_successfully(user_name):
    return f"{user_name} signed up successfully"


def logged_in_successfully(user_name):
    return f"{user_name} logged in successfully"


def modify_password_successfully(user_name):
    return f"admin user modify {user_name} password"


def group_position_lock_retry(team1, team2, retry_time, number_of_retry):
    return (
        f"error due to group position locking {team1}-{team2} after {number_of_retry} tries. "
        f"Retry in {retry_time} seconds."
    )


def modify_locking_rights(user_name, lock):
    if lock:
        return f"admin locks {user_name} bets"
    else:
        return f"admin unlocks {user_name} bets"
