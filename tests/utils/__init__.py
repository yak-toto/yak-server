import secrets
import string


def get_random_string(length: int) -> str:
    return "".join(secrets.choice(string.ascii_letters) for _ in range(length))
