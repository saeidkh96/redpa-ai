"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type EvaluationResult = {
  id: string;
  metric: string;
  score: number;
  passed: boolean;
  weight: number;
};

type EvaluationRun = {
  id: string;
  name: string;
  status: string;
  agent_id?: string | null;
  model_name?: string | null;
  aggregate_score?: number | null;
  results: EvaluationResult[];
  created_at: string;
};

type EvaluationList = {
  items: EvaluationRun[];
  total: number;
  limit: number;
  offset: number;
};

type Observability = {
  runs: {
    total: number;
    completed: number;
    failed: number;
    active: number;
    success_rate: number;
    average_aggregate_score: number;
  };
  metrics: Record<
    string,
    {
      count: number;
      passed: number;
      failed: number;
      average_score: number;
    }
  >;
  benchmarks: {
    runs: number;
    cases: number;
    passed_cases: number;
    pass_rate: number;
  };
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const DEFAULT_PAYLOAD = {
  name: "RedPA evaluation sample",
  metrics: [
    "task_success",
    "routing_accuracy",
    "tool_selection_accuracy",
    "response_relevance",
    "latency",
  ],
  input: {
    request_text: "Inspect Docker containers",
    response_text: "The Docker containers are running.",
    success: true,
    expected_route: "tool",
    actual_route: "tool",
    expected_tools: ["mcp:redpa-docker:list_containers"],
    actual_tools: ["mcp:redpa-docker:list_containers"],
    latency_ms: 850,
    latency_target_ms: 1500,
  },
  agent_id: "tool-agent",
  model_name: "qwen2.5:7b",
  pass_threshold: 0.7,
};

function score(value?: number | null) {
  if (value === null || value === undefined) return "—";
  return value.toFixed(3);
}

export default function EvaluationDashboard() {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [metrics, setMetrics] = useState<string[]>([]);
  const [observability, setObservability] = useState<Observability | null>(null);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [payload, setPayload] = useState(
    JSON.stringify(DEFAULT_PAYLOAD, null, 2),
  );

  const completed = useMemo(
    () => runs.filter((item) => item.status === "completed"),
    [runs],
  );

  const averageScore = useMemo(() => {
    const values = completed
      .map((item) => item.aggregate_score)
      .filter((item): item is number => typeof item === "number");

    if (!values.length) return null;
    return values.reduce((a, b) => a + b, 0) / values.length;
  }, [completed]);

  async function load() {
    setLoading(true);
    setNotice("");

    try {
      const [runsResponse, metricsResponse, telemetryResponse] =
        await Promise.all([
          fetch(`${API_BASE}/evaluations?limit=50`, {
            credentials: "include",
          }),
          fetch(`${API_BASE}/evaluations/metrics`, {
            credentials: "include",
          }),
          fetch(`${API_BASE}/evaluations/observability`, {
            credentials: "include",
          }),
        ]);

      if (!runsResponse.ok) {
        throw new Error(`Evaluation API: HTTP ${runsResponse.status}`);
      }
      if (!metricsResponse.ok) {
        throw new Error(`Metrics API: HTTP ${metricsResponse.status}`);
      }
      if (!telemetryResponse.ok) {
        throw new Error(`Telemetry API: HTTP ${telemetryResponse.status}`);
      }

      const runsPayload = (await runsResponse.json()) as EvaluationList;
      const metricPayload = (await metricsResponse.json()) as string[];
      const telemetryPayload =
        (await telemetryResponse.json()) as Observability;

      setRuns(runsPayload.items);
      setMetrics(metricPayload);
      setObservability(telemetryPayload);
    } catch (error) {
      setNotice(
        error instanceof Error ? error.message : "Failed to load evaluations.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setNotice("");

    try {
      const body = JSON.parse(payload);

      const response = await fetch(`${API_BASE}/evaluations`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Evaluation failed: HTTP ${response.status} ${text}`);
      }

      setNotice("Evaluation completed.");
      await load();
    } catch (error) {
      setNotice(
        error instanceof Error ? error.message : "Evaluation failed.",
      );
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <main className="evaluation-shell">
      <section className="evaluation-hero">
        <div>
          <div className="phase-kicker">PHASE 11.7</div>
          <h1>Evaluation & Benchmarking</h1>
          <p>
            Inspect evaluation quality, benchmark performance, and
            evaluation telemetry across the v3 runtime.
          </p>
        </div>

        <button onClick={() => void load()} disabled={loading}>
          {loading ? "Loading…" : "Reload"}
        </button>
      </section>

      {notice ? <div className="evaluation-notice">{notice}</div> : null}

      <section className="evaluation-stats">
        <article>
          <span>Persisted runs</span>
          <strong>{runs.length}</strong>
        </article>
        <article>
          <span>Completed</span>
          <strong>{completed.length}</strong>
        </article>
        <article>
          <span>Average score</span>
          <strong>{score(averageScore)}</strong>
        </article>
        <article>
          <span>Metrics</span>
          <strong>{metrics.length}</strong>
        </article>
      </section>

      <section className="evaluation-stats">
        <article>
          <span>Runtime evaluations</span>
          <strong>{observability?.runs.total ?? 0}</strong>
        </article>
        <article>
          <span>Runtime success rate</span>
          <strong>{score(observability?.runs.success_rate)}</strong>
        </article>
        <article>
          <span>Benchmark runs</span>
          <strong>{observability?.benchmarks.runs ?? 0}</strong>
        </article>
        <article>
          <span>Benchmark pass rate</span>
          <strong>{score(observability?.benchmarks.pass_rate)}</strong>
        </article>
      </section>

      <section className="evaluation-grid">
        <div className="evaluation-panel">
          <h2>Evaluation runs</h2>

          <div className="evaluation-run-list">
            {runs.length === 0 ? (
              <p>No evaluation runs yet.</p>
            ) : (
              runs.map((run) => (
                <article key={run.id} className="evaluation-run-card">
                  <div className="evaluation-run-head">
                    <div>
                      <strong>{run.name}</strong>
                      <span>{run.status}</span>
                    </div>
                    <div className="evaluation-score">
                      {score(run.aggregate_score)}
                    </div>
                  </div>

                  <div className="evaluation-meta">
                    {run.agent_id ? <span>{run.agent_id}</span> : null}
                    {run.model_name ? <span>{run.model_name}</span> : null}
                    <span>{new Date(run.created_at).toLocaleString()}</span>
                  </div>

                  <div className="metric-chip-row">
                    {run.results.map((result) => (
                      <span
                        className={
                          result.passed
                            ? "metric-chip metric-pass"
                            : "metric-chip metric-fail"
                        }
                        key={result.id}
                      >
                        {result.metric}: {score(result.score)}
                      </span>
                    ))}
                  </div>
                </article>
              ))
            )}
          </div>

          <h2 className="evaluation-section-title">Runtime metric telemetry</h2>
          <div className="metric-chip-row">
            {observability
              ? Object.entries(observability.metrics).map(([name, item]) => (
                  <span className="metric-chip" key={name}>
                    {name}: {score(item.average_score)} ({item.count})
                  </span>
                ))
              : null}
          </div>
        </div>

        <form className="evaluation-panel" onSubmit={submit}>
          <h2>Run evaluation</h2>
          <p>
            Edit the JSON payload and execute a new persisted evaluation.
          </p>

          <textarea
            value={payload}
            onChange={(event) => setPayload(event.target.value)}
            rows={28}
            spellCheck={false}
          />

          <button type="submit" disabled={loading}>
            Execute evaluation
          </button>
        </form>
      </section>
    </main>
  );
}
