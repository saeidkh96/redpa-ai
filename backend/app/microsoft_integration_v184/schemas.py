from pydantic import BaseModel,Field,HttpUrl
class ApprovalFlowRequest(BaseModel):
    incident_id:str; title:str; summary:str; severity:str="medium"; requested_action:str; callback_url:HttpUrl|None=None
class CopilotActionRequest(BaseModel):
    action:str=Field(pattern="^(platform_summary|agent_status|incident_summary)$"); query:str|None=None
class IntegrationEnvelope(BaseModel):
    connector:str; event_type:str; payload:dict; requires_approval:bool; audit:dict
