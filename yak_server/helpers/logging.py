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
        f"{original_bet.match.team1.description if original_bet.match.team1 else None}"
        f"-{original_bet.match.team2.description if original_bet.match.team2 else None} "
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
