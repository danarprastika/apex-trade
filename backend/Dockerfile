FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry==1.8.3
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev

FROM python:3.12-slim

RUN groupadd -r quantx && useradd -r -g quantx quantx

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ ./src/
COPY alembic/ ./alembic/

RUN chown -R quantx:quantx /app

USER quantx

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
