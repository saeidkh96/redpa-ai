# RedPA AI V7.0 Release Checklist

Run from the repository root.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements-dev.txt

cd backend
alembic upgrade head
alembic current
cd ..

python -m pytest tests -q
python scripts/security/secret_scan.py

cd frontend
npm.cmd install
npm.cmd run build
cd ..

python -m pip install -e .\sdk\python
redpa --help
redpa research --help

docker compose up -d --build
curl.exe http://localhost:8000/api/v1/health
```

Expected application version: `7.0.0`.

Then open:

```text
http://localhost:3001/control-plane/research
```

Create one research run with internet access and confirm it reaches `completed`, contains evidence, a quality result, timeline events and a final report.
