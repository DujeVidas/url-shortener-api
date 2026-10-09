FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system appuser \
    && useradd --system --gid appuser --create-home appuser

COPY pyproject.toml README.md ./
COPY app/ ./app/

RUN pip install --no-cache-dir .

USER appuser

EXPOSE 8000

CMD ["python", "-m", "app.run"]