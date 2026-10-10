# Security Policy

## Supported Versions

This project is currently maintained as a portfolio application.

Security fixes are targeted at the latest version on the `main` branch. Older versions and historical commits are not supported.

## Reporting a Vulnerability

Please do not disclose potential security vulnerabilities through public GitHub issues or pull requests.

Instead, use GitHub's private vulnerability reporting feature, if it is enabled for this repository.

To submit a private report:

1. Open the repository on GitHub.
2. Navigate to the **Security** tab.
3. Select **Report a vulnerability**, if available.
4. Describe the issue, its potential impact, and steps to reproduce it.

If private vulnerability reporting is unavailable, contact me through an appropriate private channel rather than publishing sensitive exploit details.

Do not include passwords, API keys, tokens, or other credentials in vulnerability reports.

## Security Considerations

The application implements several defensive measures, including:

- Redis-backed rate limiting for URL creation
- Request-body size limits
- Security-related HTTP response headers
- Database query and connection timeouts
- Health checks for PostgreSQL and Redis
- Non-root execution in the Docker container

These measures reduce certain risks but do not guarantee that the application is free from vulnerabilities.