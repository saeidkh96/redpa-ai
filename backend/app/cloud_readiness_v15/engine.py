from .schemas import CloudReadinessInput, CloudReadinessResult

class CloudReadinessEngine:
    def assess(self, data: CloudReadinessInput) -> CloudReadinessResult:
        checks = {
            "health_checks": data.health_checks, "dependency_checks": data.dependency_checks,
            "backups": data.backups, "restore_tested": data.restore_tested,
            "secrets_manager": data.secrets_manager, "least_privilege_iam": data.least_privilege_iam,
            "autoscaling": data.autoscaling, "capacity_tested": data.capacity_tested,
            "telemetry": data.telemetry, "alerting": data.alerting,
            "disaster_recovery": data.disaster_recovery, "multi_zone": data.multi_zone,
        }
        missing=[k for k,v in checks.items() if not v]
        score=round(sum(checks.values())/len(checks),4)
        critical = data.health_checks and data.backups and data.secrets_manager and data.telemetry
        allowed = score >= .80 and critical
        return CloudReadinessResult(environment=data.environment, score=score,
            status="ready" if allowed else "not_ready", missing_controls=missing,
            deployment_allowed=allowed)
cloud_readiness_engine=CloudReadinessEngine()
