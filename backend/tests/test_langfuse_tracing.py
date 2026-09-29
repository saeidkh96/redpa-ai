from __future__ import annotations

from app.observability.langfuse import LangfuseSettings, LangfuseTracer


def test_langfuse_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("LANGFUSE_ENABLED", raising=False)
    assert LangfuseSettings.from_environment().enabled is False


def test_disabled_tracer_is_a_safe_noop() -> None:
    tracer = LangfuseTracer(LangfuseSettings(False, True, True, "test"))
    with tracer.generation(provider="mock", model="mock-model", messages=[], metadata={}) as trace:
        trace.success(response=type("Response", (), {"content": "ok", "provider": "mock", "finish_reason": None})(), usage=None)


def test_prompt_and_output_capture_can_be_disabled() -> None:
    settings = LangfuseSettings(enabled=True, capture_inputs=False, capture_outputs=False, environment="test")
    assert settings.capture_inputs is False
    assert settings.capture_outputs is False


def test_enabled_tracer_records_provider_model_and_usage() -> None:
    class Observation:
        def __init__(self) -> None:
            self.updates: list[dict] = []
            self.ended = False

        def update(self, **kwargs) -> None:
            self.updates.append(kwargs)

        def end(self) -> None:
            self.ended = True

    class Client:
        def __init__(self) -> None:
            self.kwargs = None
            self.observation = Observation()

        def start_observation(self, **kwargs):
            self.kwargs = kwargs
            return self.observation

    client = Client()
    tracer = LangfuseTracer(LangfuseSettings(True, True, True, "test"))
    tracer._client = client
    response = type("Response", (), {"content": "answer", "provider": "ollama", "finish_reason": "stop"})()
    usage = type("Usage", (), {"input_tokens": 3, "output_tokens": 5, "total_tokens": 8})()

    with tracer.generation(provider="ollama", model="qwen2.5:7b", messages=[{"role": "user", "content": "hi"}], metadata={"agent_id": "chat"}) as trace:
        trace.success(response=response, usage=usage)

    assert client.kwargs["model"] == "qwen2.5:7b"
    assert client.kwargs["input"] == {"messages": [{"role": "user", "content": "hi"}]}
    assert client.observation.updates[0]["usage_details"]["total_tokens"] == 8
    assert client.observation.ended is True
