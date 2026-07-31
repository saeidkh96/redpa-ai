# Contributing

## Workflow

```bash
git checkout -b feature/your-feature
python -m compileall backend/app
docker compose up -d --build
docker compose logs --tail=100 backend
```

## Pull Requests

Include:

- problem statement;
- implementation approach;
- test evidence;
- documentation changes;
- migration notes.

## Commit Examples

```text
feat(tools): add datetime tool
fix(ollama): improve stream completion handling
docs: update architecture
```
