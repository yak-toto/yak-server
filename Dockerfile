# ===========================
# 1️⃣ Build Stage (uv)
# ===========================
FROM python:3.14.2-alpine3.22 AS builder

ARG COMPETITION

# Enforce it's set, or fail the build
RUN [ -n "$COMPETITION" ] || (echo "COMPETITION is required!" && false)

WORKDIR /app/

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/

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

RUN uv run yak env app --no-debug \
      # 30 minutes
      --jwt-expiration 1800 \
      # 7 days
      --jwt-refresh-expiration 604800 \
      --competition $COMPETITION

# Clean up unnecessary files from site-packages
RUN PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")') \
  && find .venv/lib/python${PYTHON_VERSION}/site-packages \
    -type d \( \
      -name "tests" -o \
      -name "testing" -o \
      -name "test" -o \
      -name "doc" -o \
      -name "docs" \
    \) \
    -exec rm -rf {} + \
  && find .venv/lib/python${PYTHON_VERSION}/site-packages \
    -type f -name "*.dist-info" -delete

# ===========================
# 2️⃣ Runtime Stage (uvicorn)
# ===========================
FROM python:3.14.2-alpine3.22 AS runtime

ARG COMPETITION

WORKDIR /app

# Copy only what the final image needs to run
COPY --from=builder /app/yak_server /app/yak_server
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/.env /app
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY docker-entrypoint.sh /usr/local/bin

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8000/api/health/ || exit 1

LABEL org.opencontainers.image.source=https://github.com/yak-toto/yak-server

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]

CMD ["uvicorn", "--factory", "yak_server:create_app", "--host", "0.0.0.0", "--workers", "4", "--port", "8000", "--timeout-keep-alive", "65"]
