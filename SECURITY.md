# Security Policy

## Supported Version

The current `main` branch is the supported development version.

## Reporting a Vulnerability

Please do not open a public issue for a suspected vulnerability.

Report security concerns to:

**Saeid Khalilian**  
`saeedkhalilian75@gmail.com`

Include:

- affected component;
- reproduction steps;
- expected and actual behavior;
- potential impact;
- suggested mitigation when available.

## Security Boundaries

RedPA includes several intentionally restrictive components.

### Filesystem MCP

- read-only access;
- sandboxed roots;
- no parent traversal;
- blocked environment and credential files;
- no arbitrary binary access.

### PostgreSQL MCP

- read-only transaction;
- SELECT, WITH, and VALUES only;
- no multiple statements;
- no SQL comments;
- no DDL or mutation;
- no row locks;
- blocked administration and filesystem functions;
- timeout and row caps.

### Docker MCP

- fixed read-only GET operations;
- no arbitrary Docker API proxy;
- no exec;
- no create;
- no stop;
- no restart;
- no remove;
- no image, volume, or network mutation.

### Human Review

Approval state is persisted and checked before sensitive workflow continuation.

## Secrets

Never commit:

- JWT secrets;
- database passwords;
- API tokens;
- GitHub tokens;
- private keys;
- `.env` files;
- production credentials.

Use environment variables and a secret manager in production.
