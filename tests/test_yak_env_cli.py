import json
from pathlib import Path
from random import randint
from uuid import uuid4

import pexpect
from dotenv import dotenv_values

from .utils import get_random_string


def test_yak_env_init():
    folder_path = Path(__file__).parent / f"test_yak_env_init/{uuid4()}"

    Path.mkdir(folder_path, parents=True, exist_ok=True)

    user_name = get_random_string(15)
    password = get_random_string(250)
    port = randint(0, 80000)
    database = get_random_string(15)

    child = pexpect.spawn("yak env init", cwd=folder_path)

    child.expect("DEBUG", timeout=10)
    child.sendline("y")

    child.expect("PROFILING", timeout=10)
    child.sendline("y")

    child.expect("MYSQL USER NAME", timeout=10)
    child.sendline(user_name)

    child.expect("MYSQL PASSWORD", timeout=10)
    child.sendline(password)

    child.expect("MYSQL PORT", timeout=10)
    child.sendline(str(port))

    child.expect("MYSQL DB", timeout=10)
    child.sendline(database)

    child.expect("JWT_EXPIRATION_TIME", timeout=10)
    child.sendline("1800")

    child.expect("world_cup_2022", timeout=10)

    child.expect("Choose your competition", timeout=10)
    child.sendline("1")

    child.expect(pexpect.EOF)

    child.close()

    assert child.exitstatus == 0
    assert child.signalstatus is None

    env = dotenv_values(folder_path / ".env")

    assert env["DEBUG"] == "1"
    assert env["PROFILING"] == "1"
    assert env["JWT_EXPIRATION_TIME"] == "1800"
    assert len(env["JWT_SECRET_KEY"]) == 256
    assert env["COMPETITION"] == "world_cup_2022"
    assert env["LOCK_DATETIME"] == "2022-11-20 17:00:00+01:00"
    assert env["BASE_CORRECT_RESULT"] == "1"
    assert env["MULTIPLYING_FACTOR_CORRECT_RESULT"] == "2"
    assert env["BASE_CORRECT_SCORE"] == "3"
    assert env["MULTIPLYING_FACTOR_CORRECT_SCORE"] == "7"
    assert env["TEAM_QUALIFIED"] == "10"
    assert env["FIRST_TEAM_QUALIFIED"] == "20"
    assert env["DATA_FOLDER"].endswith("yak_server/data/world_cup_2022")
    assert len(json.loads(env["RULES"])) == 1

    env_mysql = dotenv_values(folder_path / ".env.mysql")

    assert env_mysql["MYSQL_USER_NAME"] == user_name
    assert env_mysql["MYSQL_PASSWORD"] == password
    assert env_mysql["MYSQL_PORT"] == str(port)
    assert env_mysql["MYSQL_DB"] == database


def test_yak_env_init_default_port():
    folder_path = Path(__file__).parent / f"test_yak_env_init_default_port/{uuid4()}"

    Path.mkdir(folder_path, parents=True, exist_ok=True)

    child = pexpect.spawn("yak env init", cwd=folder_path)

    child.expect("DEBUG", timeout=10)
    child.sendline("y")

    child.expect("PROFILING", timeout=10)
    child.sendline("y")

    child.expect("MYSQL USER NAME", timeout=10)
    child.sendline("y")

    child.expect("MYSQL PASSWORD", timeout=10)
    child.sendline("y")

    child.expect("MYSQL PORT", timeout=10)
    child.sendline("")

    child.expect("MYSQL DB", timeout=10)
    child.sendline("db")

    child.expect("JWT_EXPIRATION_TIME", timeout=10)
    child.sendline("1800")

    child.expect("world_cup_2022", timeout=10)

    child.expect("Choose your competition", timeout=10)
    child.sendline("1")

    child.expect(pexpect.EOF)

    child.close()

    assert child.exitstatus == 0
    assert child.signalstatus is None

    env_mysql = dotenv_values(folder_path / ".env.mysql")

    assert "MYSQL_PORT" not in env_mysql


def test_yak_env_init_production():
    folder_path = Path(__file__).parent / f"test_yak_env_init_production/{uuid4()}"

    Path.mkdir(folder_path, parents=True, exist_ok=True)

    child = pexpect.spawn("yak env init", cwd=folder_path)

    child.expect("DEBUG", timeout=10)
    child.sendline("n")

    child.expect("MYSQL USER NAME", timeout=10)
    child.sendline("y")

    child.expect("MYSQL PASSWORD", timeout=10)
    child.sendline("y")

    child.expect("MYSQL PORT", timeout=10)
    child.sendline("3000")

    child.expect("MYSQL DB", timeout=10)
    child.sendline("db")

    child.expect("JWT_EXPIRATION_TIME", timeout=10)
    child.sendline("1800")

    child.expect("world_cup_2022", timeout=10)

    child.expect("Choose your competition", timeout=10)
    child.sendline("1")

    child.expect(pexpect.EOF)

    child.close()

    assert child.exitstatus == 0
    assert child.signalstatus is None

    env = dotenv_values(folder_path / ".env")

    assert "PROFILING" not in env
