# RedPA AI V6.0 Release Checklist

Run from the repository root unless noted.

## 1. Python environment

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
```

## 2. Database migrations

```powershell
cd backend
alembic upgrade head
alembic current
cd ..
```

## 3. Backend and repository tests

```powershell
python -m pytest tests -q
python scripts/security/secret_scan.py
```

Expected: all tests pass and the secret scan reports PASS.

## 4. SDK

```powershell
python -m pip install -e .\sdk\python
redpa --help
redpa status
redpa doctor
redpa workflows --help
redpa reviews --help
redpa mcp --help
```

Package:

```powershell
python -m pip install build
python -m build .\sdk\python
```

Expected artifacts include a `6.0.0` wheel and source distribution.

## 5. Frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run build
cd ..
```

Expected: Next.js production build succeeds.

## 6. Docker runtime

Because V6 changes backend version metadata, rebuild the runtime:

```powershell
docker compose up -d --build
docker compose ps
curl.exe http://localhost:8000/api/v1/health
```

Expected health version: `6.0.0`.

## 7. Release metadata

```powershell
git status
git diff --check
git grep -n "0.2.0"
git grep -n "6.0.0a1"
```

Any remaining old version strings must be historical/test fixtures or intentionally documented.

## 8. Commit and tag

Only after every gate above passes:

```powershell
git add .
git commit -m "release: prepare RedPA AI v6.0.0"
git push

git tag -a v6.0.0 -m "RedPA AI v6.0.0"
git push origin v6.0.0
```

Use `docs/V6_RELEASE_NOTES.md` as the basis for the GitHub Release description.
