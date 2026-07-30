# Security Policy

## Supported Versions

RedPA AI is currently in active pre-1.0 development. Security fixes are applied to the latest development version.

## Reporting a Vulnerability

Do not publish exploitable vulnerabilities in a public issue.

Contact the repository owner privately and include:

- affected component;
- reproduction steps;
- potential impact;
- suggested remediation if known.

## Security Baseline

Deployments must replace all development credentials and should:

- store secrets outside source control;
- disable debug mode;
- restrict CORS;
- use TLS;
- protect PostgreSQL, Qdrant, Prometheus, and Grafana;
- validate uploaded files;
- limit file sizes;
- isolate user retrieval data;
- enforce authorization on conversations, documents, and reviews;
- avoid logging secrets and sensitive document content;
- keep dependencies and images updated.
