FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry==1.8.3
RUN poetry install --no-interaction --no-ansi

COPY src/ ./src/

CMD ["python", "-m", "src.bot"]
