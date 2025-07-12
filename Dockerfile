# Stage 1: Builder
FROM python:3.13.5-alpine3.22 AS builder

ARG COMPETITION
ARG APP_VERSION

# Enforce it's set, or fail the build
RUN [ -n "$COMPETITION" ] || (echo "COMPETITION is required!" && false)
RUN [ -n "$APP_VERSION" ] || (echo "APP_VERSION is required!" && false)

WORKDIR /app/

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.7.11 /uv /uvx /bin/

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=scripts/build_hooks.py,target=scripts/build_hooks.py \
    uv sync --locked --no-install-project --no-dev --all-extras

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY yak_server /app/yak_server
COPY alembic.ini /app/alembic.ini

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=scripts/build_hooks.py,target=scripts/build_hooks.py \
    uv sync --locked --no-dev --all-extras

RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    [ "$APP_VERSION" = "$(uv version --short)" ] || (echo "$APP_VERSION != "$(uv version --short)"" && false)

RUN uv run yak env app --no-debug --jwt-expiration 1800 --competition $COMPETITION

# Clean up unnecessary files from site-packages
RUN mv .venv/lib/python3.13/site-packages/pendulum/testing \
         .venv/lib/python3.13/site-packages/pendulum/keep_this_one \
  && find .venv/lib/python3.13/site-packages \
    -type d \( \
      -name "tests" -o \
      -name "testing" -o \
      -name "test" -o \
      -name "doc" -o \
      -name "docs" \
    \) \
    -exec rm -rf {} + \
  && find .venv/lib/python3.13/site-packages \
    -type f -name "*.dist-info" -delete \
  && mv .venv/lib/python3.13/site-packages/pendulum/keep_this_one \
          .venv/lib/python3.13/site-packages/pendulum/testing

# Stage 2: Runtime
FROM python:3.13.5-alpine3.22 AS runtime

ARG COMPETITION
ARG APP_VERSION
ARG BUILD_DATE

LABEL org.opencontainers.image.title="Yak Server"
LABEL org.opencontainers.image.description="Football bet rest/graphql server"
LABEL org.opencontainers.image.version=$APP_VERSION
LABEL org.opencontainers.image.source="https://github.com/yak-toto/yak-server"
LABEL org.opencontainers.image.created=$BUILD_DATE

WORKDIR /app

# Copy only what the final image needs to run
COPY --from=builder /app/yak_server /app/yak_server
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/.env /app
COPY --from=builder /app/alembic.ini /app/alembic.ini

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8000/api/health/ || exit 1

ENTRYPOINT ["uvicorn", "--factory" , "yak_server:create_app","--host", "0.0.0.0", "--workers", "4", "--port"]

CMD ["8000"]
