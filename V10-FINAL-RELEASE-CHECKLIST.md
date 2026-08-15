# RedPA AI v10.0.0 Final Release Checklist

## Already verified
- [x] V10 governance tests pass
- [x] V10 runtime integration tests pass
- [x] V10 Ops governance tests pass
- [x] V10 Phase 3.1 lifecycle tests pass
- [x] V10 release-hardening tests pass
- [x] Full Python suite: 344 passed
- [x] Frontend production build passes
- [x] `docker compose config --quiet` passes
- [x] Primary Compose stack includes Policy Service
- [x] Backend health reports `10.0.0`
- [x] Ops Agent health reports `10.0.0`
- [x] Policy Service health reports `UP`
- [x] Governed recovery E2E reaches `COMPLETED`
- [x] E2E evaluation score is `1.0`

## Before commit
- [ ] Copy the V10 changelog entry to the top of existing `CHANGELOG.md`
- [ ] Remove temporary audit files if they should not be tracked
- [ ] `git status --short`
- [ ] `python -m pytest tests -q`
- [ ] `python scripts/security/secret_scan.py`
- [ ] `docker compose config --quiet`

## Release commit
```bash
git add .
git commit -m "release: RedPA AI v10.0.0 governed agent runtime"
```

## Tag
```bash
git tag -a v10.0.0 -m "RedPA AI v10.0.0 - Governed Agent Runtime"
git push origin main
git push origin v10.0.0
```

## GitHub release
Use `docs/releases/V10.0.0.md` as the release description.

Recommended title:

```text
RedPA AI v10.0.0 — Governed Agent Runtime
```
