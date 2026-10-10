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