# Base image with uv + deps
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base-deps

WORKDIR /app

# COPY pyproject.toml uv.lock ./
COPY pyproject.toml ./
RUN apt-get update && apt-get install -y libgomp1 build-essential git \
# && uv sync --locked --no-install-project --no-dev \
&& apt-get clean && rm -rf /var/lib/apt/lists/*

# Builder
FROM base-deps AS builder

COPY services/candles /app/services/candles
COPY services/predictor /app/services/predictor
COPY services/technical_indicators /app/services/technical_indicators
COPY . /app

RUN uv sync --locked --no-editable --no-dev

# Cleaner
FROM python:3.12-slim-bookworm AS cleaner

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/services/predictor /app/services/predictor

RUN find /app/.venv -name '*.pyc' -delete && \
    find /app/.venv -name '__pycache__' -delete && \
    rm -rf /app/.venv/share /app/.venv/include /app/.venv/lib/python3.12/test

# Runtime
FROM python:3.12-slim-bookworm

ENV PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=cleaner /app/.venv /app/.venv
COPY --from=cleaner /app/services/predictor /app/services/predictor

CMD ["python", "/app/services/predictor/src/predictor/train.py"]
