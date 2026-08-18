from .schemas import ConnectorRiskInput,ConnectorRiskResult
class ConnectorRiskEngine:
    def assess(self,x:ConnectorRiskInput)->ConnectorRiskResult:
        score=0; reasons=[]
        for cond,pts,msg in [(x.write_access,25,"write_access"),(x.external_network,15,"external_network"),(x.handles_secrets,30,"handles_secrets"),(not x.scoped_credentials,20,"unscoped_credentials"),(not x.audit_logging,15,"missing_audit_logging"),(not x.rate_limited,10,"missing_rate_limit")]:
            if cond: score+=pts; reasons.append(msg)
        score=min(score,100); level="low" if score<25 else "medium" if score<50 else "high" if score<75 else "critical"
        decision="allow" if score<50 else ("review" if x.approval_required or score<75 else "block")
        return ConnectorRiskResult(connector=x.connector,risk_score=score,risk_level=level,decision=decision,reasons=reasons)
connector_risk_engine=ConnectorRiskEngine()
