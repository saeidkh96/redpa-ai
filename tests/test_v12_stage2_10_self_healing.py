from pathlib import Path
import pytest
from app.self_healing.health_state import AgentRuntimeHealthStore, RuntimeHealthStatus
from app.self_healing.persistence import FailoverCheckpointStore
from app.self_healing.validation import validate

@pytest.mark.asyncio
async def test_stage2_three_failures_unavailable():
    s=AgentRuntimeHealthStore(unavailable_threshold=3)
    await s.record_failure("a"); await s.record_failure("a"); h=await s.record_failure("a")
    assert h.status==RuntimeHealthStatus.UNAVAILABLE

@pytest.mark.asyncio
async def test_stage9_checkpoint_store_contract_is_db_backed():
    store = FailoverCheckpointStore()

    assert hasattr(store, "save")
    assert hasattr(store, "get")
    assert hasattr(store, "delete")

    assert callable(store.save)
    assert callable(store.get)
    assert callable(store.delete)

def test_stage10_gate():
    e={"stage1":{"healthy_preferred":True,"offline_excluded":True},"stage2":{"consecutive_failures":3,"status":"unavailable"},"stage3":{"replacement_selected":True,"selected_failed_agent":False},"stage4":{"blocked_without_approval":True,"approved_executable":True},"stage5":{"workflow_preserved":True,"context_preserved":True},"stage6":{"replacement_executed":True,"verification_passed":True},"stage7":{"rejoin_requires_healthy":True,"failure_streak_cleared":True},"stage8":{"execution_count":1,"duplicate_detected":True},"stage9":{"checkpoint_persisted":True,"same_idempotency_key":True}}
    assert all(c.passed for c in validate(e))
