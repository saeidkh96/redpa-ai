# Langfuse in RedPA AI

RedPA records one Langfuse generation for each provider attempt in the central
`ModelGateway`. This covers Ollama, OpenAI-compatible, Anthropic, Gemini, and
fallback routing without adding tracing code to each agent.

## Setup

1. Create a project in Langfuse and copy its public and secret keys.
2. Add the values to your untracked `.env` file:

```env
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_TRACING_ENVIRONMENT=development
```

3. Rebuild and start the backend:

```powershell
docker compose up -d --build backend
```

Every model call will then include the routed provider/model, request messages,
response, token usage when supplied by the provider, latency, agent metadata,
fallback attempts, and errors.

## Privacy controls

Set either value to `false` to avoid sending prompt content or generated output:

```env
LANGFUSE_CAPTURE_INPUTS=false
LANGFUSE_CAPTURE_OUTPUTS=false
```

The feature is disabled by default. Missing credentials or a Langfuse outage
never blocks RedPA's model gateway.
