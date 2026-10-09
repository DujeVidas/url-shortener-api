FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system appuser \
    && useradd --system --gid appuser --create-home appuser

COPY pyproject.toml README.md alembic.ini ./
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY scripts/start.sh ./scripts/start.sh

RUN pip install --no-cache-dir .

USER appuser

EXPOSE 8000

CMD ["sh", "scripts/start.sh"]