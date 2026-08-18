# V12 Self-Healing Multi-Agent

Target lifecycle:

`agent failure -> failure record -> capability discovery -> health-aware replacement -> policy -> optional approval -> context handoff -> replacement execution -> verification -> checkpoint -> recovery -> controlled rejoin`

Design rules: reuse the existing A2A registry, never select the failed agent as its own replacement, fail closed on verification failure, keep high-risk failover approval-aware, make duplicate failovers idempotent, and persist restart checkpoints.
