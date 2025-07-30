# Security Policy

## Secret Management

- **Never** commit real API keys or credentials.
- For GitHub Actions, add secrets in the repository settings and expose them as environment variables in the workflow.
- With Docker Compose, configure `env_file: .env` so secrets are loaded from your local `.env` file.
- In PyCharm, set variables under Run/Debug Configuration → Environment.

See [`.env.example`](./.env.example) for the required variables.
