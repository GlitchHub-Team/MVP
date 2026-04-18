FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml . 

RUN uv pip install --system playwright pytest nats-py psycopg[binary] nkeys
RUN playwright install --with-deps chromium

CMD ["tail", "-f", "/dev/null"]