from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class Check:
    name: str
    passed: bool
def validate_v14_evidence(e):
    checks = [
        Check("Stage 1 control registry", bool(e.get("stage1",{}).get("control_versioned"))),
        Check("Stage 2 evidence collection", bool(e.get("stage2",{}).get("evidence_persisted"))),
        Check("Stage 3 completeness", bool(e.get("stage3",{}).get("missing_detected"))),
        Check("Stage 4 integrity", bool(e.get("stage4",{}).get("hash_verified"))),
        Check("Stage 5 freshness", bool(e.get("stage5",{}).get("expiry_enforced"))),
        Check("Stage 6 risk assessment", bool(e.get("stage6",{}).get("risk_scored"))),
        Check("Stage 7 approval boundary", bool(e.get("stage7",{}).get("high_risk_requires_approval"))),
        Check("Stage 8 audit record", bool(e.get("stage8",{}).get("record_persisted"))),
        Check("Stage 9 export", bool(e.get("stage9",{}).get("export_verified"))),
    ]
    checks.append(Check("Stage 10 readiness gate", all(c.passed for c in checks)))
    return checks
