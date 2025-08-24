FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy uv configuration
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY metrolinkTimes/ ./metrolinkTimes/

# Copy config directory (you can override this with a volume mount)
COPY config/ ./config/

# Create log directory
RUN mkdir -p /var/log/metrolinkTimes

# Expose port
EXPOSE 5000

# Run the FastAPI application with uv
CMD ["uv", "run", "python", "-m", "metrolinkTimes"]