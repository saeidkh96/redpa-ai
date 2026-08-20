from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(
        encoding="utf-8"
    )


def test_v191_governance_analytics_contract():
    service = read(
        "backend/app/enterprise_analytics_v191/service.py"
    )

    api = read(
        "backend/app/api/v1/"
        "enterprise_analytics_v191.py"
    )

    assert "AgentRun" in service
    assert "AgentRunEvent" in service
    assert "HumanReview" in service

    assert "approval_rate_percent" in service
    assert "average_decision_latency_seconds" in service
    assert "approval.requested" in service
    assert "approval.approved" in service

    assert 'prefix="/analytics/v19.1"' in api
    assert '"/kpis"' in api
    assert '"/evidence"' in api
    assert '"/capabilities"' in api


def test_v191_microsoft_governance_linkage_contract():
    service = read(
        "backend/app/"
        "microsoft_integration_v191/service.py"
    )

    assert "approval.requested" in service
    assert "approval_granted" in service
    assert "approved_review_id" in service
    assert "resume_run" in service


def test_v191_aws_foundation_contract():
    aws = read("infra/aws/__main__.py")

    assert "aws.ec2.Vpc" in aws
    assert "aws.ecs.Cluster" in aws
    assert "aws.ecr.Repository" in aws
    assert "aws.cloudwatch.LogGroup" in aws

    # V19.1 currently validates a deployed AWS
    # foundation. It must not claim an ECS service
    # deployment until that is implemented.
    assert "aws.ecs.Service" not in aws


def test_v191_aws_policy_contract():
    policy = read(
        "infra/aws/"
        "redpa-v191-deployment-policy.json"
    )

    assert "ec2:CreateVpc" in policy
    assert "ecs:CreateCluster" in policy
    assert "ecr:CreateRepository" in policy
    assert "logs:CreateLogGroup" in policy


def test_v191_router_registration():
    router = read(
        "backend/app/api/v1/router.py"
    )

    assert "microsoft_integration_v191_router" in router
    assert "enterprise_analytics_v191_router" in router

def test_v191_resume_metric_uses_event_sequence():
    service = read(
        "backend/app/enterprise_analytics_v191/service.py"
    )

    assert 'event.event_type == "approval.approved"' in service
    assert 'event.event_type == "run.running"' in service
    assert "resumed_run_ids" in service
