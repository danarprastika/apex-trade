FROM python:3.12-slim AS builder

WORKDIR /app

COPY telegram/pyproject.toml ./
RUN pip install --no-cache-dir --prefix=/install -e ".[dev]"

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY telegram/ ./

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
