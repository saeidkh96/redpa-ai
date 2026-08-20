from fastapi import APIRouter
from app.api.dependencies import CurrentUser
from app.microsoft_integration_v184.schemas import ApprovalFlowRequest,CopilotActionRequest,IntegrationEnvelope
from app.microsoft_integration_v184.service import microsoft_integration_service
router=APIRouter(prefix="/integrations/microsoft/v18.4",tags=["V18.4 Microsoft Integration"])
@router.post("/power-automate/approval",response_model=IntegrationEnvelope)
async def power_automate_approval(payload:ApprovalFlowRequest,current_user:CurrentUser): return microsoft_integration_service.power_automate_approval(payload)
@router.post("/copilot-studio/action")
async def copilot_action(payload:CopilotActionRequest,current_user:CurrentUser): return microsoft_integration_service.copilot_action(payload)
@router.get("/capabilities")
async def capabilities(current_user:CurrentUser): return {"power_automate":{"approval_contract":True,"teams_outlook_ready":True},"copilot_studio":{"rest_actions":True},"m365_copilot":{"integration_contract":True},"credentials_embedded":False}
