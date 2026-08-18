from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Check:
    name: str
    passed: bool

def validate(e):
    checks = [
        Check("Stage 1 routing", bool(e.get("stage1",{}).get("healthy_preferred")) and bool(e.get("stage1",{}).get("offline_excluded"))),
        Check("Stage 2 failure tracking", int(e.get("stage2",{}).get("consecutive_failures",0)) >= 3 and e.get("stage2",{}).get("status") == "unavailable"),
        Check("Stage 3 fallback", bool(e.get("stage3",{}).get("replacement_selected")) and not bool(e.get("stage3",{}).get("selected_failed_agent"))),
        Check("Stage 4 governance", bool(e.get("stage4",{}).get("blocked_without_approval")) and bool(e.get("stage4",{}).get("approved_executable"))),
        Check("Stage 5 handoff", bool(e.get("stage5",{}).get("workflow_preserved")) and bool(e.get("stage5",{}).get("context_preserved"))),
        Check("Stage 6 execution", bool(e.get("stage6",{}).get("replacement_executed")) and bool(e.get("stage6",{}).get("verification_passed"))),
        Check("Stage 7 rejoin", bool(e.get("stage7",{}).get("rejoin_requires_healthy")) and bool(e.get("stage7",{}).get("failure_streak_cleared"))),
        Check("Stage 8 idempotency", int(e.get("stage8",{}).get("execution_count",0)) == 1 and bool(e.get("stage8",{}).get("duplicate_detected"))),
        Check("Stage 9 persistence", bool(e.get("stage9",{}).get("checkpoint_persisted")) and bool(e.get("stage9",{}).get("same_idempotency_key"))),
    ]
    checks.append(Check("Stage 10 gate", all(c.passed for c in checks)))
    return checks
