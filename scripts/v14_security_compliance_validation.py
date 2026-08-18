from __future__ import annotations
import json, sys
from pathlib import Path
from app.security_compliance_v14.validation import validate_v14_evidence
INPUT=Path("artifacts/v14-security-compliance-validation-input.json")
OUTPUT=Path("artifacts/v14-security-compliance-validation.json")
def main():
    path=Path(sys.argv[1]) if len(sys.argv)>1 else INPUT
    if not path.exists():
        print(f"[ERROR] Evidence file not found: {path}"); return 2
    checks=validate_v14_evidence(json.loads(path.read_text(encoding="utf-8-sig")))
    print("RedPA AI V14 Security & Compliance Validation")
    print("="*46)
    for c in checks: print(f"[{'PASS' if c.passed else 'FAIL'}] {c.name}")
    passed=all(c.passed for c in checks)
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps({"version":"14.0.0","validation":"PASS" if passed else "FAIL","checks":[{"name":c.name,"passed":c.passed} for c in checks]},indent=2),encoding="utf-8")
    print()
    print(f"SECURITY & COMPLIANCE VALIDATION: {'PASS' if passed else 'FAIL'}")
    print(f"Evidence report: {OUTPUT}")
    return 0 if passed else 1
if __name__=="__main__": raise SystemExit(main())
