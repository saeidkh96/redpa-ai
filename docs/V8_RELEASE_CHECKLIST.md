# RedPA AI V8.0 Release Checklist

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install -e .\sdk\python

# Database migration inside Docker network (recommended on Docker Desktop)
docker compose up -d postgres
docker compose run --rm --build `
  -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai" `
  -e JWT_SECRET_KEY="redpa-local-v8-release-key" `
  backend python -m alembic upgrade head

docker compose run --rm `
  -e DATABASE_URL="postgresql+asyncpg://postgres:postgres@postgres:5432/redpa_ai" `
  -e JWT_SECRET_KEY="redpa-local-v8-release-key" `
  backend python -m alembic current

python -m pytest tests -q
python scripts/security/secret_scan.py
git diff --check

cd frontend
npm.cmd install
npm.cmd run build
cd ..

docker compose up -d --build
curl.exe http://localhost:8000/api/v1/health
python scripts/reliability/load_test.py --base-url http://localhost:8000
```

Expected migration head: `v80a1b2c3d4e`.

Expected application version: `8.0.0`.

Manual UI checks:

- `/control-plane/research`
- `/control-plane/analytics`
- `/control-plane/connectors`
- `/control-plane/operations`

For connector live execution, use a test endpoint and verify dry-run first. Do not commit connector secrets.
