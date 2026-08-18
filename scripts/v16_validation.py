from __future__ import annotations
import json,sys
from pathlib import Path
from app.continuous_evaluation_v16.validation import validate
INPUT=Path("artifacts/v16-validation-input.json"); OUTPUT=Path("artifacts/v16-validation.json")
def main():
 p=Path(sys.argv[1]) if len(sys.argv)>1 else INPUT
 if not p.exists(): print(f"[ERROR] Evidence file not found: {p}"); return 2
 checks=validate(json.loads(p.read_text(encoding="utf-8-sig")))
 print("RedPA AI V16 Agent Evaluation & Continuous Improvement Validation"); print("="*48)
 for c in checks: print(f"[{'PASS' if c.passed else 'FAIL'}] {c.name}")
 passed=all(c.passed for c in checks); OUTPUT.parent.mkdir(parents=True,exist_ok=True)
 OUTPUT.write_text(json.dumps({"version":"16.0.0","validation":"PASS" if passed else "FAIL","checks":[{"name":c.name,"passed":c.passed} for c in checks]},indent=2),encoding="utf-8")
 print(f"VALIDATION: {'PASS' if passed else 'FAIL'}"); return 0 if passed else 1
if __name__=="__main__": raise SystemExit(main())
