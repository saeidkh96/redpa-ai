"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Result = { metric: string; score: number; passed: boolean };
type Run = {
  id: string;
  name: string;
  status: string;
  aggregate_score?: number | null;
  pass_threshold: number;
  agent_id?: string | null;
  model_name?: string | null;
  created_at: string;
  results: Result[];
};
type RunList = { items: Run[]; total: number };
type Delta = {
  metric: string;
  baseline_score?: number | null;
  candidate_score?: number | null;
  delta?: number | null;
  regressed: boolean;
};
type Regression = {
  baseline_run_id: string;
  candidate_run_id: string;
  baseline_score: number;
  candidate_score: number;
  aggregate_delta: number;
  metric_deltas: Delta[];
  regressed_metrics: string[];
  regression_detected: boolean;
};
type Gate = {
  id: string;
  decision: string;
  reasons: string[];
  release_label?: string | null;
  regression: Regression;
  created_at: string;
};
type ReleaseGateHistoryItem = {
  id: string;
  baseline_run_id: string;
  candidate_run_id: string;
  release_label?: string | null;
  decision: string;
  reasons: string[];
  baseline_score: number;
  candidate_score: number;
  aggregate_delta: number;
  regression_detected: boolean;
  regressed_metrics: string[];
  created_at: string;
};
type ReleaseGateHistory = { items: ReleaseGateHistoryItem[]; total: number };
type BenchmarkTrend = {
  id: string;
  name: string;
  agent_id?: string | null;
  model_name?: string | null;
  aggregate_score: number;
  pass_rate: number;
  metric_averages: Record<string, number>;
  created_at: string;
};
type BenchmarkTrendResponse = { items: BenchmarkTrend[]; total: number };

type Benchmark = {
  id: string;
  name: string;
  agent_id?: string | null;
  model_name?: string | null;
  aggregate_score: number;
  pass_rate: number;
  pass_threshold: number;
  metric_averages: Record<string, number>;
  created_at: string;
};
type BenchmarkList = { items: Benchmark[]; total: number };
type ProviderReliability = {
  provider: string;
  available: boolean;
  circuit_state: string;
  failures: number;
  failure_threshold: number;
  score: number;
  status: string;
};
type ReliabilityScorecard = {
  overall_score: number;
  healthy_providers: number;
  degraded_providers: number;
  unavailable_providers: number;
  providers: ProviderReliability[];
};
type FailureSimulation = {
  primary_attempts: number;
  fallback_attempted: boolean;
  recovered: boolean;
  expected_outcome: string;
  events: string[];
};

export default function ReliabilityEvaluationPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [baseline, setBaseline] = useState("");
  const [candidate, setCandidate] = useState("");
  const [maxAggregateDrop, setMaxAggregateDrop] = useState("0.05");
  const [maxMetricDrop, setMaxMetricDrop] = useState("0.10");
  const [minimumScore, setMinimumScore] = useState("0.70");
  const [releaseLabel, setReleaseLabel] = useState("candidate-release");
  const [gate, setGate] = useState<Gate | null>(null);
  const [gateHistory, setGateHistory] = useState<ReleaseGateHistoryItem[]>([]);
  const [trends, setTrends] = useState<BenchmarkTrend[]>([]);
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
  const [scorecard, setScorecard] = useState<ReliabilityScorecard | null>(null);
  const [simulation, setSimulation] = useState<FailureSimulation | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [runResult, benchmarkResult, reliabilityResult, gateHistoryResult, trendResult] = await Promise.allSettled([
        redpaFetch<RunList>("/api/v1/evaluations?limit=100"),
        redpaFetch<BenchmarkList>("/api/v1/evaluations/benchmark-history?limit=100"),
        redpaFetch<ReliabilityScorecard>("/api/v1/model-gateway/reliability/scorecard", {}, true),
        redpaFetch<ReleaseGateHistory>("/api/v1/evaluations/release-gates?limit=100"),
        redpaFetch<BenchmarkTrendResponse>("/api/v1/evaluations/benchmark-trends?limit=100"),
      ]);
      if (runResult.status === "fulfilled") {
        const payload = runResult.value;
        setRuns(payload.items);
        if (!baseline && payload.items.length > 1) setBaseline(payload.items[1].id);
        if (!candidate && payload.items.length) setCandidate(payload.items[0].id);
      } else {
        throw runResult.reason;
      }
      if (benchmarkResult.status === "fulfilled") setBenchmarks(benchmarkResult.value.items);
      if (reliabilityResult.status === "fulfilled") setScorecard(reliabilityResult.value);
      if (gateHistoryResult.status === "fulfilled") setGateHistory(gateHistoryResult.value.items);
      if (trendResult.status === "fulfilled") setTrends(trendResult.value.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load evaluation runs");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  async function evaluate() {
    if (!baseline || !candidate) return;
    setEvaluating(true);
    setError("");
    try {
      const payload = {
        baseline_run_id: baseline,
        candidate_run_id: candidate,
        max_aggregate_drop: Number(maxAggregateDrop),
        max_metric_drop: Number(maxMetricDrop),
        minimum_candidate_score: Number(minimumScore),
        require_candidate_pass: true,
        release_label: releaseLabel.trim() || null,
        metadata: { source: "control-plane" },
      };
      setGate(await redpaFetch<Gate>("/api/v1/evaluations/release-gates/evaluate", {
        method: "POST",
        body: JSON.stringify(payload),
      }));
      await load();
    } catch (err) {
      setGate(null);
      setError(err instanceof Error ? err.message : "Quality gate evaluation failed");
    } finally {
      setEvaluating(false);
    }
  }

  async function simulateFailure() {
    setError("");
    try {
      setSimulation(await redpaFetch<FailureSimulation>("/api/v1/model-gateway/reliability/simulate", {
        method: "POST",
        body: JSON.stringify({
          primary_failures: 2,
          retry_attempts: 2,
          fallback_available: true,
          primary_retryable: true,
        }),
      }, true));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failure simulation failed");
    }
  }

  const completed = useMemo(() => runs.filter((r) => r.status === "completed"), [runs]);
  const avg = useMemo(() => {
    const scores = completed.map((r) => r.aggregate_score).filter((v): v is number => typeof v === "number");
    return scores.length ? scores.reduce((a,b) => a+b,0)/scores.length : null;
  }, [completed]);

  return <>
    <header className="cpHeader">
      <div><p className="cpEyebrow">REDPA AI · V5.5</p><h1>Evaluation & Reliability</h1><p>Compare persisted evaluation runs, detect regressions and enforce explicit quality gates before promoting an agent or model change.</p></div>
      <button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
    </header>

    {error ? <div className="cpNotice">{error}</div> : null}

    <section className="cpMetrics">
      <MetricCard label="Persisted runs" value={runs.length} />
      <MetricCard label="Completed" value={completed.length} />
      <MetricCard label="Average score" value={avg == null ? "—" : avg.toFixed(3)} />
      <MetricCard label="Last quality gate" value={gate?.decision || "—"} />
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Regression gate</span><h2>Baseline vs candidate</h2></div>{gate ? <StatusBadge value={gate.decision} /> : null}</div>
      <div className="cpReliabilityForm">
        <label><span>Baseline</span><select value={baseline} onChange={(e) => setBaseline(e.target.value)}><option value="">Select baseline</option>{runs.map((run) => <option key={run.id} value={run.id}>{run.name} · {run.aggregate_score?.toFixed(3) ?? "—"}</option>)}</select></label>
        <label><span>Candidate</span><select value={candidate} onChange={(e) => setCandidate(e.target.value)}><option value="">Select candidate</option>{runs.map((run) => <option key={run.id} value={run.id}>{run.name} · {run.aggregate_score?.toFixed(3) ?? "—"}</option>)}</select></label>
        <label><span>Max aggregate drop</span><input value={maxAggregateDrop} onChange={(e) => setMaxAggregateDrop(e.target.value)} /></label>
        <label><span>Max metric drop</span><input value={maxMetricDrop} onChange={(e) => setMaxMetricDrop(e.target.value)} /></label>
        <label><span>Minimum score</span><input value={minimumScore} onChange={(e) => setMinimumScore(e.target.value)} /></label>
        <label><span>Release label</span><input value={releaseLabel} onChange={(e) => setReleaseLabel(e.target.value)} /></label>
      </div>
      <div className="cpActions"><button onClick={() => void evaluate()} disabled={evaluating || !baseline || !candidate}>{evaluating ? "Evaluating…" : "Evaluate & persist release gate"}</button></div>
    </section>

    {gate ? <>
      <section className="cpMetrics">
        <MetricCard label="Baseline score" value={gate.regression.baseline_score.toFixed(3)} />
        <MetricCard label="Candidate score" value={gate.regression.candidate_score.toFixed(3)} />
        <MetricCard label="Aggregate delta" value={gate.regression.aggregate_delta.toFixed(3)} />
        <MetricCard label="Regressed metrics" value={gate.regression.regressed_metrics.length} />
      </section>
      <section className="cpPanel">
        <div className="cpPanelHead"><div><span>Decision</span><h2>{gate.decision}</h2></div><StatusBadge value={gate.decision} /></div>
        <div className={gate.decision === "PASS" ? "cpSuccess" : "cpNotice"}>{gate.reasons.join(" · ")}</div>
        <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Metric</th><th>Baseline</th><th>Candidate</th><th>Delta</th><th>Status</th></tr></thead><tbody>
          {gate.regression.metric_deltas.map((item) => <tr key={item.metric}><td><strong>{item.metric}</strong></td><td>{item.baseline_score?.toFixed(3) ?? "—"}</td><td>{item.candidate_score?.toFixed(3) ?? "—"}</td><td>{item.delta?.toFixed(3) ?? "—"}</td><td><StatusBadge value={item.regressed ? "regressed" : "stable"} /></td></tr>)}
        </tbody></table></div>
      </section>
    </> : null}

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Promotion history</span><h2>Release quality gates</h2></div><span>{gateHistory.length} decisions</span></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Time</th><th>Release</th><th>Decision</th><th>Baseline</th><th>Candidate</th><th>Delta</th><th>Reasons</th></tr></thead><tbody>
        {gateHistory.map((item) => <tr key={item.id}><td>{new Date(item.created_at).toLocaleString()}</td><td><strong>{item.release_label || "—"}</strong><small>{item.id}</small></td><td><StatusBadge value={item.decision} /></td><td>{item.baseline_score.toFixed(3)}</td><td>{item.candidate_score.toFixed(3)}</td><td>{item.aggregate_delta.toFixed(3)}</td><td>{item.reasons.join(", ")}</td></tr>)}
      </tbody></table></div>
      {!gateHistory.length ? <p className="cpMuted">No persisted release-gate decisions yet.</p> : null}
      <p className="cpMuted">CI can call <code>POST /api/v1/evaluations/release-gates/ci-check</code>; failed gates return HTTP 409.</p>
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Historical quality</span><h2>Benchmark trend</h2></div><span>{trends.length} points</span></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Time</th><th>Benchmark</th><th>Agent</th><th>Model</th><th>Score</th><th>Pass rate</th></tr></thead><tbody>
        {trends.map((item) => <tr key={item.id}><td>{new Date(item.created_at).toLocaleString()}</td><td><strong>{item.name}</strong></td><td>{item.agent_id || "—"}</td><td>{item.model_name || "—"}</td><td>{item.aggregate_score.toFixed(3)}</td><td>{(item.pass_rate * 100).toFixed(1)}%</td></tr>)}
      </tbody></table></div>
      {!trends.length ? <p className="cpMuted">Persisted benchmark runs will appear here chronologically.</p> : null}
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Provider resilience</span><h2>Reliability scorecard</h2></div>{scorecard ? <StatusBadge value={scorecard.unavailable_providers ? "degraded" : "healthy"} /> : null}</div>
      <section className="cpMetrics">
        <MetricCard label="Overall reliability" value={scorecard ? scorecard.overall_score.toFixed(3) : "—"} />
        <MetricCard label="Healthy providers" value={scorecard?.healthy_providers ?? "—"} />
        <MetricCard label="Degraded" value={scorecard?.degraded_providers ?? "—"} />
        <MetricCard label="Unavailable" value={scorecard?.unavailable_providers ?? "—"} />
      </section>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Provider</th><th>Status</th><th>Score</th><th>Circuit</th><th>Failures</th></tr></thead><tbody>
        {(scorecard?.providers || []).map((item) => <tr key={item.provider}><td><strong>{item.provider}</strong></td><td><StatusBadge value={item.status} /></td><td>{item.score.toFixed(3)}</td><td><StatusBadge value={item.circuit_state} /></td><td>{item.failures} / {item.failure_threshold}</td></tr>)}
      </tbody></table></div>
      <div className="cpActions"><button onClick={() => void simulateFailure()}>Validate retry + fallback scenario</button></div>
      {simulation ? <div className={simulation.recovered ? "cpSuccess" : "cpNotice"}><strong>{simulation.expected_outcome}</strong> · {simulation.events.join(" → ")}</div> : null}
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Persisted benchmark history</span><h2>Agent / model comparison pool</h2></div><span>{benchmarks.length} runs</span></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Benchmark</th><th>Agent</th><th>Model</th><th>Score</th><th>Pass rate</th><th>Created</th></tr></thead><tbody>
        {benchmarks.map((item) => <tr key={item.id}><td><strong>{item.name}</strong><small>{item.id}</small></td><td>{item.agent_id || "—"}</td><td>{item.model_name || "—"}</td><td>{item.aggregate_score.toFixed(3)}</td><td>{(item.pass_rate * 100).toFixed(1)}%</td><td>{new Date(item.created_at).toLocaleString()}</td></tr>)}
      </tbody></table></div>
      {!benchmarks.length ? <p className="cpMuted">Benchmark runs created through the benchmark API will be persisted here after the V5.5 migration is applied.</p> : null}
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Evaluation history</span><h2>Candidate pool</h2></div></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Run</th><th>Status</th><th>Score</th><th>Threshold</th><th>Agent</th><th>Model</th><th>Created</th></tr></thead><tbody>
        {runs.map((run) => <tr key={run.id}><td><strong>{run.name}</strong><small>{run.id}</small></td><td><StatusBadge value={run.status} /></td><td>{run.aggregate_score?.toFixed(3) ?? "—"}</td><td>{run.pass_threshold.toFixed(2)}</td><td>{run.agent_id || "—"}</td><td>{run.model_name || "—"}</td><td>{new Date(run.created_at).toLocaleString()}</td></tr>)}
      </tbody></table></div>
    </section>
  </>;
}
