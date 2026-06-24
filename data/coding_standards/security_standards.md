# Security Coding Standards

## Authentication
- Always use established libraries for authentication.
- Never implement custom cryptographic algorithms.
- Validate JWT tokens on every protected endpoint.

## Input Validation
- Validate all inputs at the API boundary.
- Use allowlists for input validation where possible.
- Never trust data from the client.

## Database Security
- Always use parameterized queries.
- Encrypt sensitive fields at rest.
- Restrict database users to minimum permissions.

## Secrets Management
- Store secrets in environment variables only.
- Never commit .env files to version control.
- Rotate API keys regularly.

## API Security
- Rate-limit all public API endpoints.
- Return generic error messages to clients.
- Use HTTPS only.
- Set proper CORS headers.

## Logging
- Log all authentication attempts.
- Never log passwords, tokens, or PII.