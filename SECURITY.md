# Security Policy

## Supported Version

The current `main` branch is the supported development version.

## Reporting a Vulnerability

Do not open a public issue for a suspected vulnerability.

Report security concerns to:

**Saeid Khalilian**  
`saeedkhalilian75@gmail.com`

Include:

- affected component;
- reproduction steps;
- expected and actual behavior;
- potential impact;
- relevant logs;
- suggested mitigation when available.

## Security Architecture

RedPA applies security at the API, workflow, tool, MCP, A2A, persistence, and infrastructure layers.

## Authentication

- OAuth2 password flow;
- JWT access tokens;
- current-user boundaries;
- protected application endpoints;
- no credentials embedded in Agent or MCP URLs.

## Planner and Workflow Safety

- deterministic safety patterns;
- explicit route selection;
- Human Review for sensitive workflows;
- approval state checked before continuation;
- A2A discovery intent evaluated before MCP execution intent;
- no distributed execution before required approval.

## Filesystem MCP

- read-only access;
- sandboxed roots;
- parent traversal rejection;
- environment and credential files blocked;
- binary files rejected;
- no arbitrary filesystem access.

## PostgreSQL MCP

- read-only transactions;
- `SELECT`, `WITH`, and `VALUES` only;
- no multiple statements;
- no SQL comments;
- no DDL;
- no mutation;
- no row locks;
- blocked administration and filesystem functions;
- query timeout;
- row limits.

## Docker MCP

- fixed read-only GET operations;
- no arbitrary Docker API proxy;
- no `exec`;
- no create;
- no stop;
- no restart;
- no kill;
- no remove;
- no image, network, or volume mutation.

## A2A Security

Remote A2A connections are subject to:

- explicit Remote Agent registration;
- HTTP or HTTPS URL validation;
- no embedded URL credentials;
- Agent Card resolution before delegation;
- enabled-state checks;
- bounded request timeouts;
- structured task metadata;
- approval policy before sensitive Multi-Agent execution.

The current development setup uses Docker service discovery:

```text
http://a2a-coordinator:8050
```

For production:

- require TLS;
- authenticate Remote Agents;
- restrict Agent allowlists;
- validate Agent Card ownership;
- apply network policies;
- add retry and circuit-breaker policies;
- persist and audit Remote Agent configuration.

## Human Review

The normal LangGraph Human Review flow persists approval state and checks it before workflow continuation.

The Multi-Agent approval gate stops high-risk distributed requests before any Remote Agent is contacted.

## Secrets

Never commit:

- JWT secrets;
- database passwords;
- API tokens;
- GitHub tokens;
- private keys;
- `.env` files;
- production credentials;
- external Agent credentials.

Use environment variables and a managed secret store in production.

## Dependency Security

Pin security-sensitive dependencies and review compatibility constraints.

The current A2A SDK integration requires a compatible Protobuf major version:

```text
a2a-sdk[http-server]==1.0.2
protobuf>=6,<7
```

## Production Checklist

Before deployment:

- disable debug mode;
- rotate secrets;
- restrict CORS;
- enable TLS;
- protect Grafana and Prometheus;
- remove unnecessary published ports;
- use non-default database credentials;
- review Docker socket access;
- use least-privilege service accounts;
- enable backups;
- configure centralized logging;
- add distributed tracing;
- validate Remote Agent trust boundaries.
