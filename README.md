# URL Shortener API

[![CI](https://github.com/DujeVidas/url-shortener-api/actions/workflows/ci.yml/badge.svg)](https://github.com/DujeVidas/url-shortener-api/actions/workflows/ci.yml)

A production-style URL shortening and analytics REST API built with **FastAPI, PostgreSQL, Redis, and Docker**.

The application converts long URLs into short links, redirects visitors to their original destinations, and tracks usage analytics. It includes Redis-backed caching and rate limiting, structured error responses, health checks, and automated testing.

## Features

- **URL shortening:** Generate unique short codes for long URLs.
- **Custom aliases:** Create memorable short links with custom codes.
- **URL redirection:** Redirect visitors to their original destinations.
- **Protected analytics:** View URL usage statistics using a management token.
- **Protected URL deactivation:** Disable links using a management token without deleting their database records.
- **Management-token security:** Generate a unique token per URL and store only its SHA-256 hash.
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

## API Reference

The API provides endpoints for creating shortened URLs, redirecting visitors, viewing analytics, and deactivating links.

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/urls` | Create a shortened URL |
| `GET` | `/{short_code}` | Redirect to the original URL |
| `GET` | `/api/v1/urls/{short_code}/analytics` | Retrieve URL analytics |
| `DELETE` | `/api/v1/urls/{short_code}` | Deactivate a shortened URL |
| `GET` | `/health/live` | Check whether the application is running |
| `GET` | `/health/ready` | Check PostgreSQL and Redis readiness |
| `GET` | `/api/v1/version` | Retrieve application version information |

### Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **OpenAPI schema:** http://localhost:8000/openapi.json

Swagger UI allows developers to inspect request schemas, response models, status codes, and rate-limit headers.

### Create a Short URL

Send a POST request with the original URL:

```bash
curl -i -X POST http://localhost:8000/api/v1/urls \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'
```

The response also includes a unique `management_token`. Save this token securely when creating the URL because it is required to view analytics and deactivate the link.

The API generates a cryptographically random token and stores only its SHA-256 hash in PostgreSQL. The original token cannot be retrieved from the database.

**Important:** Treat the management token as a secret. Do not include it in public URLs, query parameters, logs, or source control. If the token is lost, it cannot be recovered.

### Redirect to the Original URL

Replace `SHORT_CODE` with a code returned by the creation endpoint:

```bash
curl -i http://localhost:8000/SHORT_CODE
```

A successful redirect returns an HTTP redirect response with a `Location` header pointing to the original URL.

### View Analytics

```bash
curl -i \
  -H "X-Management-Token: YOUR_MANAGEMENT_TOKEN" \
  http://localhost:8000/api/v1/urls/SHORT_CODE/analytics
```

The analytics endpoint returns usage information for the shortened URL.

A valid `X-Management-Token` header is required. Missing or invalid tokens return HTTP `403 Forbidden`. Unknown short codes return HTTP `404 Not Found`.

Historical analytics remain accessible with the correct management token after a URL has been deactivated.

### Deactivate a URL

```bash
curl -i -X DELETE \
  -H "X-Management-Token: YOUR_MANAGEMENT_TOKEN" \
  http://localhost:8000/api/v1/urls/SHORT_CODE
```

A successful deactivation returns HTTP `204 No Content`.

Deactivated URLs remain in the database but are no longer available for normal redirection.

Deactivation requires the same management token returned when the URL was created.

Missing or invalid tokens return HTTP `403 Forbidden` without deactivating the URL. Unknown or already-deactivated URLs return HTTP `404 Not Found`.

Public redirects do not require management tokens.

**Legacy URLs:** URLs created before management tokens were introduced have no stored token hash. They can still redirect while active, but protected analytics and deactivation operations are unavailable for those URLs.

### Rate Limiting

URL creation is protected by Redis-backed rate limiting.

Successful creation responses include:

- `RateLimit-Limit` — maximum requests allowed per window.
- `RateLimit-Remaining` — requests remaining in the current window.
- `RateLimit-Reset` — seconds until the window resets.

If the limit is exceeded, the API returns HTTP `429 Too Many Requests` with a `Retry-After` header.

If the rate-limiting service is unavailable, URL creation returns HTTP `503 Service Unavailable`.

The default Docker Compose configuration allows **10 URL creation requests per 60 seconds**.

## Development

### Requirements

For local Python development, install:

- Python 3.12 or newer
- Docker and Docker Compose
- Git

Docker Compose provides PostgreSQL and Redis, while Python runs the development tools locally.

### Create a Virtual Environment

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

### Install Development Dependencies

```bash
python -m pip install -e ".[dev]"
```

This installs the application and its development tools, including pytest, Ruff, and coverage reporting.

### Start Supporting Services

Start PostgreSQL and Redis:

```bash
docker compose --env-file .env.compose up -d db redis
```

The `.env.compose` file can be created from `.env.compose.example` as described in the Getting Started section.

### Run Tests

```bash
python -m pytest -v
```

Some tests require a running Redis instance. Starting the supporting services beforehand allows these integration tests to execute.

### Run Tests with Branch Coverage

```bash
python -m pytest -v --cov=app --cov-branch --cov-report=term-missing
```

The project enforces a minimum of **90% combined statement and branch coverage**.

### Lint and Format

Check Python code quality:

```bash
python -m ruff check app tests
```

Check formatting without modifying files:

```bash
python -m ruff format --check app tests
```

Automatically fix supported linting issues:

```bash
python -m ruff check app tests --fix
```

Apply consistent formatting:

```bash
python -m ruff format app tests
```

### Database Migrations

The Dockerized API automatically applies migrations on startup.

To inspect the current database revision:

```bash
docker compose --env-file .env.compose exec api alembic current
```

To inspect the latest available revision:

```bash
docker compose --env-file .env.compose exec api alembic heads
```

For normal Docker Compose startup, no manual migration command is necessary.

### Continuous Integration

GitHub Actions automatically runs Ruff linting, formatting checks, and pytest with branch coverage on pushes and pull requests.

The workflow is defined in `.github/workflows/ci.yml`.

### Development Shortcuts

A Makefile provides shortcuts for common development tasks.

```bash
make help
```

Run all code-quality checks and tests:

```bash
make check
```

Other useful commands:

| Command | Description |
|---|---|
| `make install` | Install development dependencies |
| `make lint` | Run Ruff linting |
| `make format` | Format Python code |
| `make format-check` | Check formatting |
| `make test` | Run pytest |
| `make coverage` | Run tests with branch coverage |

The `make check` command runs linting, formatting verification, and tests with the project's minimum 90% coverage requirement.

The `make ci` command runs the same linting, formatting, and coverage checks used by the project's GitHub Actions workflow:

```bash
make ci
```

Run it before pushing changes to catch quality issues locally.


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.