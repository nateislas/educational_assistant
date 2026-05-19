FROM python:3.11-slim

# Copy the uv binary from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install python dependencies using uv (ultra fast, no build-essential needed)
COPY requirements.txt .
RUN uv pip install --no-cache --system -r requirements.txt

# Copy source code (this is overridden by bind mount in dev, but good for self-contained builds)
COPY src/ ./src/

CMD ["python", "src/agent.py"]
