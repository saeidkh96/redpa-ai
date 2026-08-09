# RedPA AI v3 — Phase 12.1 / 12.2 / 12.3

## 12.1 Provider Interface + SOLID Foundation
Adds a provider-neutral `LLMProvider` contract, normalized request/response types, capabilities, health and errors.

## 12.2 Provider Adapters
Adds Ollama, OpenAI-compatible, and deterministic Mock adapters. Existing RedPA `LLMService` is intentionally left untouched in this phase, so current chat/RAG/workflows keep working while the gateway is introduced beside them.

## 12.3 Factory + Registry
Adds configuration-driven provider creation, default-provider selection, enabled/disabled providers, capability filtering, Factory Pattern and Registry Pattern.

Existing RedPA environment values remain compatible:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT_SECONDS=120
```

Optional new values:

```env
MODEL_GATEWAY_DEFAULT_PROVIDER=ollama
MODEL_GATEWAY_OLLAMA_ENABLED=true
MODEL_GATEWAY_OPENAI_COMPATIBLE_ENABLED=false
OPENAI_COMPATIBLE_PROVIDER_NAME=openai-compatible
OPENAI_COMPATIBLE_BASE_URL=https://api.openai.com
OPENAI_COMPATIBLE_MODEL=gpt-4.1-mini
OPENAI_COMPATIBLE_API_KEY=
OPENAI_COMPATIBLE_TIMEOUT_SECONDS=120
```

Keep the OpenAI-compatible provider disabled until you intentionally configure a compatible endpoint/key.

## Verify

```powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_12_1_12_3.ps1
```

No database migration is required.
