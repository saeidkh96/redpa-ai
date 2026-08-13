# Release Guide

## Current release

**RedPA AI v6.0.0 — Developer Platform**

Use the evidence-based V6 release documents:

- [`V6_RELEASE_NOTES.md`](V6_RELEASE_NOTES.md)
- [`V6_RELEASE_CHECKLIST.md`](V6_RELEASE_CHECKLIST.md)
- [`V6_RELEASE_AUDIT.md`](V6_RELEASE_AUDIT.md)
- [`V6_REPOSITORY_CLEANUP.md`](V6_REPOSITORY_CLEANUP.md)

## Release process

1. Apply Alembic migrations.
2. Run the full Python test suite.
3. Run the repository secret scan.
4. Build the Next.js frontend.
5. Build/install the Python SDK and smoke-test the CLI.
6. Rebuild the Docker Compose runtime and verify `/api/v1/health`.
7. Confirm release metadata reports `6.0.0`.
8. Review `git diff --check` and repository status.
9. Tag only after every release gate passes.

```bash
git tag -a v6.0.0 -m "RedPA AI v6.0.0"
git push origin v6.0.0
```

Deployment/reference assets such as Azure/Pulumi and Kubernetes/Helm must not be described as a live production deployment unless separately deployed and validated.
