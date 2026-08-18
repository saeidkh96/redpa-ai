from app.enterprise_integration_v17.engine import connector_risk_engine
from app.enterprise_integration_v17.schemas import ConnectorRiskInput
def test_v17_low_risk():
 r=connector_risk_engine.assess(ConnectorRiskInput(connector="internal",external_network=False)); assert r.decision=="allow"
def test_v17_high_risk_requires_boundary():
 r=connector_risk_engine.assess(ConnectorRiskInput(connector="external",write_access=True,handles_secrets=True,scoped_credentials=False)); assert r.decision in {"review","block"}
