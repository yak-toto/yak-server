# 🐂 Yak-toto

**The REST API behind Yak-toto — a football score-prediction game for World Cups and Euros.**

Friends bet on match scores and group standings, points are computed automatically, and a live leaderboard settles the argument.

[![PyPI](https://img.shields.io/pypi/v/yak-server?label=stable)](https://pypi.org/project/yak-server/)
[![Docker Image](https://img.shields.io/badge/Docker-ghcr.io-blue?logo=docker)](https://github.com/yak-toto/yak-server/pkgs/container/yak-server)
[![Python Versions](https://img.shields.io/pypi/pyversions/yak-server)](https://pypi.org/project/yak-server/)
[![codecov](https://codecov.io/gh/yak-toto/yak-server/branch/main/graph/badge.svg?token=EZZK5SY5BL)](https://codecov.io/gh/yak-toto/yak-server)
[![Testing](https://github.com/yak-toto/yak-server/actions/workflows/test.yml/badge.svg)](https://github.com/yak-toto/yak-server/actions/workflows/test.yml)
[![🔐 CodeQL](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

______________________________________________________________________

## ✨ Features

- ⚽ **Bet on real tournaments** — World Cup 2018/2022/2026 and Euro 2016/2020/2024 data ship out of the box, ready to load.
- 🧮 **Automatic scoring** — bets on match scores, binary bets, and group-ranking bets are graded against official results as they come in.
- 🏆 **Live score board** — a computed leaderboard ranks every player as results are entered.
- 🔐 **Secure by default** — JWT access + refresh tokens, Argon2 password hashing, invite-token-gated signup, and per-route rate limiting.
- 🚀 **Modern async-ready stack** — [FastAPI](https://fastapi.tiangolo.com/) + [SQLAlchemy 2](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/) on PostgreSQL.
- 🖥️ **Batteries-included CLI** — the `yak` command handles env setup, database lifecycle, migrations, admin creation, and score board generation.
- 🐳 **Container-first** — official multi-arch images published to GHCR, one per competition.
- 📄 **Self-documenting API** — interactive Swagger UI and ReDoc generated straight from the code.

## 🏗️ Tech stack

| Layer | Choice |
| -------------- | ------------------------------------------ |
| API framework | FastAPI + Pydantic v2 |
| Database | PostgreSQL, via SQLAlchemy 2 + Alembic |
| Auth | PyJWT (access + refresh) + Argon2 |
| Rate limiting | slowapi |
| Packaging | uv + hatchling |
| CLI | Click |
| Tests | pytest, pytest-cov |

## 🚀 Quickstart

### Requisites

- Python ≥ 3.10
- PostgreSQL (a ready-to-run container is provided via `docker-compose.dev.yml`)
- [uv](https://docs.astral.sh/uv/)

### 1. Install dependencies

```bash
uv sync --all-groups
```

### 2. Configure your environment

`yak env all` walks you through the configuration and writes `.env` and `.env.db` for you (JWT secrets, JWT lifetimes, and the competition to load).

```bash
uv run yak env all
```

Signup is gated behind an invite token to prevent unwanted account creation. Set `SIGNUP_TOKEN` in `.env` to a short alphanumeric value and share it out-of-band with people you want to let sign up — they must send it as `signup_token` in the signup request body.

```text
SIGNUP_TOKEN=A1B2C3
```

### 3. Start PostgreSQL

```bash
docker compose -f docker-compose.dev.yml up -d
```

### 4. Set up the database

```bash
uv run yak db create    # create tables
uv run yak db init      # load competition data
uv run yak db admin     # create an admin account
```

### 5. Run the API

```bash
uv run uvicorn --reload --factory yak_server:create_app
```

The API is now live at `http://localhost:8000/api`, with interactive docs at `/api/docs` and `/api/redoc`.

> A [`justfile`](justfile) wraps all of the above (and more) into short commands — try `just setup`, `just run`, `just test`.

## 🐳 Run with Docker

Prebuilt images are published to GHCR, one per competition:

```bash
docker run -p 8000:8000 \
  -e JWT_SECRET_KEY=... -e JWT_REFRESH_SECRET_KEY=... \
  -e POSTGRES_HOST=... -e POSTGRES_USER=... -e POSTGRES_PASSWORD=... -e POSTGRES_DB=... \
  -e SIGNUP_TOKEN=... \
  ghcr.io/yak-toto/yak-server:0.93.1-world_cup_2026
```

Images are tagged `<version>-<competition>`; browse available tags on [GHCR](https://github.com/yak-toto/yak-server/pkgs/container/yak-server).

See [`Dockerfile`](Dockerfile) and [`docker-compose.ci.yml`](docker-compose.ci.yml) for a complete example including PostgreSQL.

## 🛠️ The `yak` CLI

| Command | Description |
| ----------------------- | ----------------------------------------------- |
| `yak env all` | Interactively generate `.env` and `.env.db` |
| `yak env app` | Generate only the app `.env` file |
| `yak env db` | Generate only the database `.env.db` file |
| `yak db create` | Create database tables |
| `yak db init` | Load competition data |
| `yak db admin` | Create an admin account |
| `yak db drop` | Drop all tables |
| `yak db delete` | Delete all records |
| `yak db migration` | Help run Alembic migration scripts |
| `yak db score-board` | Recompute the score board |
| `yak openapi` | Print the OpenAPI schema as JSON |

Run `uv run yak --help` for the full reference.

## 🧪 Testing

```bash
just test        # pytest
just test-cov     # pytest with HTML coverage report
```

## 📊 Profiling

Run the app with a profiler attached:

```bash
just run_profiling
```

## 🤝 Contributing

Issues and pull requests are welcome! Please run `just check` (pre-commit: lint, format, type-checking) before submitting.

## 📄 License

[MIT](LICENSE) © Guillaume Le Pape
