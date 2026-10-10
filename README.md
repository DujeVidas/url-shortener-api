# URL Shortener API

[![CI](https://github.com/DujeVidas/url-shortener-api/actions/workflows/ci.yml/badge.svg)](https://github.com/DujeVidas/url-shortener-api/actions/workflows/ci.yml)

A production-style URL shortening and analytics REST API built with **FastAPI, PostgreSQL, Redis, and Docker**.

The application converts long URLs into short links, redirects visitors to their original destinations, and tracks usage analytics. It includes Redis-backed caching and rate limiting, structured error responses, health checks, and automated testing.

## Features

- **URL shortening:** Generate unique short codes for long URLs.
- **Custom aliases:** Create memorable short links with custom codes.
- **URL redirection:** Redirect visitors to their original destinations.
- **Click analytics:** Track usage statistics for shortened URLs.
- **URL deactivation:** Disable links without deleting their database records.
- **Redis caching:** Reduce database queries for frequently accessed links.
- **Rate limiting:** Protect URL creation using Redis-backed request limits.
- **Health checks:** Separate liveness and readiness endpoints, including database and Redis connectivity.
- **API documentation:** Interactive Swagger UI and an OpenAPI specification.
- **Automated testing:** pytest, Redis integration tests, and OpenAPI contract validation.
- **Continuous integration:** GitHub Actions with Ruff linting, formatting, and a minimum 90% test coverage requirement.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application language |
| FastAPI | REST API framework |
| PostgreSQL | Persistent data storage |
| SQLAlchemy | Database ORM |
| Alembic | Database migrations |
| Redis | Caching and rate limiting |
| Docker Compose | Local service orchestration |
| pytest | Automated testing |
| Ruff | Linting and formatting |
| GitHub Actions | Continuous integration |

## Project Status

**Actively developed.**

The core URL shortening, analytics, caching, rate limiting, health checks, and automated testing features are implemented.

The CI pipeline enforces a minimum of **90% combined statement and branch coverage**.

## Getting Started

### Prerequisites

To run the application locally, you need:

- **Git** — to clone the repository.
- **Docker** — to run the application and its services.
- **Docker Compose** — to orchestrate FastAPI, PostgreSQL, and Redis.

Python does not need to be installed locally when using Docker Compose.

### Clone the Repository

```bash
git clone https://github.com/DujeVidas/url-shortener-api.git
cd url-shortener-api
```

### Configure Environment Variables

Copy the example environment file:

```bash
cp .env.compose.example .env.compose
```

Open `.env.compose` and review the configuration.

The environment file contains the settings needed to connect the application to PostgreSQL and Redis.

Do not commit `.env.compose` to Git because it may contain credentials.

### Start the Application

Build and start the services:

```bash
docker compose --env-file .env.compose up --build -d
```

This starts the FastAPI application, PostgreSQL database, and Redis.

**Database migrations:** The API container automatically runs `alembic upgrade head` before starting FastAPI. On the first startup, Alembic creates the database schema. On subsequent startups, it applies any pending migrations. No manual migration command is required.

### Verify the Application

Once the containers are running, open:

- **Swagger UI:** http://localhost:8000/docs
- **OpenAPI schema:** http://localhost:8000/openapi.json
- **Liveness:** http://localhost:8000/health/live
- **Readiness:** http://localhost:8000/health/ready

The readiness endpoint checks whether the application can communicate with its required database and Redis services.

You can also check readiness from the terminal:

```bash
curl -i http://localhost:8000/health/ready
```

A healthy application returns HTTP `200` with:

```json
{
  "status": "ready"
}
```

### View Container Logs

```bash
docker compose --env-file .env.compose logs -f api
```

Press `Ctrl+C` to stop following the logs.

### Stop the Application

```bash
docker compose --env-file .env.compose down
```

This stops and removes the containers and network while preserving named database volumes.

**Warning:** Do not use `docker compose down -v` unless you intentionally want to delete the database volumes and their stored data.