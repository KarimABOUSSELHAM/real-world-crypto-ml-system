# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Copy project metadata
COPY pyproject.toml uv.lock ./
COPY . /app

# Enable bytecode compilation and copy mode for uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install C/C++ libraries required for building Python packages
RUN apt-get update && apt-get install -y libgomp1

# Install dependencies from lockfile (reproducible)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev
    # uv sync --frozen --no-dev

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run your script
CMD ["uv", "run", "services/predictor/src/predictor/predict.py"]
