# RedPA AI V9.0 Release Checklist

```powershell
python -m pytest tests -q
python scripts/security/secret_scan.py
git diff --check

cd frontend
npm.cmd install
npm.cmd run build
cd ..

docker compose up -d --build
docker compose exec backend python -m alembic upgrade head
docker compose exec backend python -m alembic current
curl.exe http://localhost:8000/api/v1/health
curl.exe http://localhost:8070/health
```

Expected application version: `9.0.0`.

Validate Control Plane routes:

- `http://localhost:3001/control-plane/incidents`
- `http://localhost:3001/control-plane/cloud`
- `http://localhost:3001/control-plane/cost`

Run a diagnosis first. Execute restart remediation only for an allowlisted stateless RedPA service and only after explicit approval.
