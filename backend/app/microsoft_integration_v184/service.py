from datetime import datetime,timezone
from .schemas import ApprovalFlowRequest,CopilotActionRequest,IntegrationEnvelope
class MicrosoftIntegrationService:
 def power_automate_approval(self,x:ApprovalFlowRequest):
  return IntegrationEnvelope(connector="power-automate",event_type="redpa.approval.requested",payload=x.model_dump(mode="json"),requires_approval=True,audit={"generated_at":datetime.now(timezone.utc).isoformat(),"boundary":"human-approval"})
 def copilot_action(self,x:CopilotActionRequest):
  return {"connector":"copilot-studio","action":x.action,"query":x.query,"status":"ready","note":"Action contract is credential-free; bind it to a Copilot Studio REST action in the target tenant."}
microsoft_integration_service=MicrosoftIntegrationService()
