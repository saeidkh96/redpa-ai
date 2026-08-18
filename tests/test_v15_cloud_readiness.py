from app.cloud_readiness_v15.engine import cloud_readiness_engine
from app.cloud_readiness_v15.schemas import CloudReadinessInput
def test_v15_ready():
 x=CloudReadinessInput(environment="prod",health_checks=True,dependency_checks=True,backups=True,restore_tested=True,secrets_manager=True,least_privilege_iam=True,autoscaling=True,capacity_tested=True,telemetry=True,alerting=True,disaster_recovery=True,multi_zone=True)
 r=cloud_readiness_engine.assess(x); assert r.deployment_allowed and r.score==1.0
def test_v15_fail_closed_on_missing_backup():
 x=CloudReadinessInput(environment="prod"); r=cloud_readiness_engine.assess(x); assert not r.deployment_allowed
