from setuptools import setup

setup(
    name="Yak Toto",
    version="1.0",
    long_description=__doc__,
    packages=["server"],
    install_requires=[
        "Flask-SQLAlchemy >= 2.5",
        "Flask-Cors >= 3.0",
        "requests >= 2.25",
        "PyJWT >= 2.4.0",
        "PyMySQL >= 1.0.2",
        "python-dotenv >= 0.20.0",
    ],
)
