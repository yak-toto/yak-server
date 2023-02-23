from getpass import getpass


class ConfirmPasswordDoesNotMatch(Exception):
    def __init__(self) -> None:
        super().__init__("Password and Confirm Password fields does not match.")


class SignupError(Exception):
    def __init__(self, description) -> None:
        super().__init__(f"Error during signup. {description}")


def script(app):
    with app.app_context():
        password = getpass(prompt="Admin user password: ")
        confirm_password = getpass(prompt="Confirm admin password: ")

        if password != confirm_password:
            raise ConfirmPasswordDoesNotMatch

        client = app.test_client()

        response_signup = client.post(
            "/api/v1/users/signup",
            json={
                "name": "admin",
                "first_name": "admin",
                "last_name": "admin",
                "password": password,
            },
        )

        if not response_signup.json["ok"]:
            raise SignupError(response_signup.json["description"])
