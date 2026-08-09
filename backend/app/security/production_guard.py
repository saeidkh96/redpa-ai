from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductionFinding:
    code: str
    severity: str
    message: str


def evaluate_production_configuration(
    env: dict[str, str],
) -> tuple[ProductionFinding, ...]:
    findings: list[ProductionFinding] = []

    environment = env.get("ENVIRONMENT", "").lower()
    production = environment == "production"

    if not production:
        return ()

    if env.get("DEBUG", "").lower() in {"1", "true", "yes", "on"}:
        findings.append(
            ProductionFinding(
                code="PROD_DEBUG_ENABLED",
                severity="critical",
                message="DEBUG must be disabled in production.",
            )
        )

    if env.get("EXPOSE_ERROR_DETAILS", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        findings.append(
            ProductionFinding(
                code="PROD_ERROR_DETAILS",
                severity="high",
                message="Detailed internal errors must not be exposed.",
            )
        )

    if env.get("REQUIRE_HTTPS", "").lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        findings.append(
            ProductionFinding(
                code="PROD_HTTPS_REQUIRED",
                severity="critical",
                message="HTTPS enforcement must be enabled.",
            )
        )

    secret = env.get("JWT_SECRET_KEY") or env.get("SECRET_KEY") or ""
    if len(secret) < 32:
        findings.append(
            ProductionFinding(
                code="PROD_WEAK_JWT_SECRET",
                severity="critical",
                message="JWT/secret key must be at least 32 characters.",
            )
        )

    allowed_hosts = env.get("ALLOWED_HOSTS", "").strip()
    if not allowed_hosts or allowed_hosts == "*":
        findings.append(
            ProductionFinding(
                code="PROD_ALLOWED_HOSTS",
                severity="high",
                message="Production ALLOWED_HOSTS must be explicit.",
            )
        )

    cors = env.get("CORS_ORIGINS", "").strip()
    if cors == "*":
        findings.append(
            ProductionFinding(
                code="PROD_WILDCARD_CORS",
                severity="high",
                message="Wildcard CORS is not allowed in production.",
            )
        )

    return tuple(findings)


def assert_production_configuration(
    env: dict[str, str],
) -> None:
    findings = evaluate_production_configuration(env)
    blocking = [
        finding
        for finding in findings
        if finding.severity in {"critical", "high"}
    ]

    if blocking:
        details = "; ".join(
            f"{item.code}: {item.message}"
            for item in blocking
        )
        raise RuntimeError(
            f"Production configuration rejected: {details}"
        )
