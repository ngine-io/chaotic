# Build the virtualenv in a throwaway stage, so that neither uv nor the sources
# end up in the published image.
FROM docker.io/python:3.14.7-slim AS builder

# Pin uv by copying its binary out of the official (scratch based) uv image.
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Build in /app, the same path the venv will live at in the final image: the
# console script's shebang is an absolute path and would otherwise dangle.
WORKDIR /app

# Install the dependencies first: this layer is only rebuilt when the lock file
# changes, not on every source edit.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable --no-dev


FROM docker.io/python:3.14.7-slim

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY docker/config.yaml ./config.yaml

USER 1000

ENTRYPOINT ["chaotic-ngine"]
