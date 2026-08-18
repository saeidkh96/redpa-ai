from pydantic import BaseModel, Field
class ConnectorRiskInput(BaseModel):
    connector:str=Field(min_length=1,max_length=150)
    write_access:bool=False
    external_network:bool=True
    handles_secrets:bool=False
    approval_required:bool=False
    scoped_credentials:bool=True
    audit_logging:bool=True
    rate_limited:bool=True
class ConnectorRiskResult(BaseModel):
    connector:str; risk_score:int; risk_level:str; decision:str; reasons:list[str]
