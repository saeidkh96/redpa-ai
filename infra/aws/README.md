# RedPA AI V20 — AWS Production Infrastructure

Pulumi infrastructure for the validated RedPA AI AWS development and production stacks in `eu-central-1`. V20 introduces a dedicated `prod` stack while preserving the existing `dev` resource identities and zero-drift behavior.

## Production topology

```text
Internet -> ALB -> ECS/Fargate (2–4 tasks) -> private RDS PostgreSQL
                    |
                    +-> Redis sidecar per task
                    +-> CloudWatch Logs / Container Insights
ECR -> ECS
Secrets Manager -> runtime
CloudWatch alarms -> SNS production alert topic
Application Auto Scaling -> ECS desired count
```

## V20 production contract

- release/runtime: `20.0.0` / `production`
- production image tag: `v20.0.0`
- ECS minimum/steady-state capacity: `2`
- ECS maximum capacity: `4`
- CPU target tracking: `60%`
- memory target tracking: `70%`
- scale-out cooldown: `60s`
- scale-in cooldown: `300s`
- private encrypted RDS with deletion protection
- RDS Multi-AZ: `false`
- RDS backup retention: `1 day`
- seven CloudWatch alarms
- SNS alarm-action routing
- optional email subscription through `alert_email` configuration
- final production preview: `39 unchanged`

## Stack usage

```powershell
cd infra/aws
python -m pip install -r requirements.txt

pulumi stack select dev
pulumi preview

pulumi stack select prod
pulumi preview
```

Use `pulumi up` only after reviewing the selected stack and preview. Production secrets are Pulumi secret configuration values and should never be committed as plaintext.

## Deployment boundaries

V20 validates a real production AWS runtime, but does not claim HTTPS/custom-domain ingress, WAF, Multi-AZ RDS, regional failover, multi-region HA, or an SLA/SLO. The production SNS topic is deployed and alarm actions are connected; an email subscriber is only created when explicitly configured.
