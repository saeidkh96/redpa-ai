# RedPA AI V19 — AWS Foundation

Pulumi foundation for an AWS deployment: VPC, ECS cluster with Container Insights, ECR with scan-on-push and CloudWatch Logs. This is intentionally a foundation, not a claim that the public production deployment is already running.

```bash
cd infra/aws
pip install -r requirements.txt
pulumi stack init dev
pulumi up
```
