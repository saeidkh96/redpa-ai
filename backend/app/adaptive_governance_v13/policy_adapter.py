from __future__ import annotations

from typing import Any

from app.models.adaptive_governance_v13 import AdaptivePolicyProposal


class PolicyApplicationAdapter:
    """
    Integration seam for RedPA's existing persisted policy override / Java policy path.

    V13 never silently auto-applies recommendations. The current implementation
    records an explicit approved applied-state envelope. Wire this adapter to the
    existing policy override service once its exact write API is selected.
    """

    async def apply(self, proposal: AdaptivePolicyProposal) -> dict[str, Any]:
        return {
            "action": proposal.action,
            "decision": proposal.recommended_decision,
            "risk": proposal.recommended_risk,
            "proposal_id": str(proposal.id),
            "version": proposal.version,
            "explicitly_approved": True,
            "auto_applied": False,
        }

    async def rollback(
        self,
        *,
        proposal: AdaptivePolicyProposal,
        previous_state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "proposal_id": str(proposal.id),
            "restored": previous_state,
            "rollback": True,
        }


policy_application_adapter = PolicyApplicationAdapter()
