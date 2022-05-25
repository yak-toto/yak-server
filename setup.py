from setuptools import setup

setup(
    name="Yak Toto",
    version="1.0",
    long_description=__doc__,
    packages=["server"],
    install_requires=[
        "Flask-Login >= 0.5",
        "Flask-SQLAlchemy >= 2.5",
        "requests >= 2.25",
    ],
)
