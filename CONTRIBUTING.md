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
feat(tools): add weather tool
fix(planner): normalize unsupported route
docs: update API guide
```
