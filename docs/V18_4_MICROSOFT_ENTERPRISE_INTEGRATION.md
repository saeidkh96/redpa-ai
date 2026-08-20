# RedPA AI V18.4 — Microsoft Enterprise Integration

V18.4 adds credential-free integration contracts for Power Automate, Power Platform, Copilot Studio and Microsoft 365 scenarios. It does **not** claim a tenant connection by default.

## Reference flow
`RedPA incident -> Power Automate approval -> Teams/Outlook -> human decision -> RedPA governed action -> audit evidence`

Copilot Studio can bind REST actions to RedPA for platform summaries, agent status and incident summaries. Production tenant credentials remain external secrets.
