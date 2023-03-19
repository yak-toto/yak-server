import random
import string


def get_random_string(length, letters=None):
    if letters is None:
        letters = string.ascii_letters

    return "".join(random.choice(string.ascii_letters) for _ in range(length))
