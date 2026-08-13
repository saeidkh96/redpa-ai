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
type Gate = { decision: string; reasons: string[]; regression: Regression };

export default function ReliabilityEvaluationPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [baseline, setBaseline] = useState("");
  const [candidate, setCandidate] = useState("");
  const [maxAggregateDrop, setMaxAggregateDrop] = useState("0.05");
  const [maxMetricDrop, setMaxMetricDrop] = useState("0.10");
  const [minimumScore, setMinimumScore] = useState("0.70");
  const [gate, setGate] = useState<Gate | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const payload = await redpaFetch<RunList>("/api/v1/evaluations?limit=100");
      setRuns(payload.items);
      if (!baseline && payload.items.length > 1) setBaseline(payload.items[1].id);
      if (!candidate && payload.items.length) setCandidate(payload.items[0].id);
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
      };
      setGate(await redpaFetch<Gate>("/api/v1/evaluations/quality-gates/evaluate", {
        method: "POST",
        body: JSON.stringify(payload),
      }));
    } catch (err) {
      setGate(null);
      setError(err instanceof Error ? err.message : "Quality gate evaluation failed");
    } finally {
      setEvaluating(false);
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
      </div>
      <div className="cpActions"><button onClick={() => void evaluate()} disabled={evaluating || !baseline || !candidate}>{evaluating ? "Evaluating…" : "Run quality gate"}</button></div>
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
      <div className="cpPanelHead"><div><span>Evaluation history</span><h2>Candidate pool</h2></div></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Run</th><th>Status</th><th>Score</th><th>Threshold</th><th>Agent</th><th>Model</th><th>Created</th></tr></thead><tbody>
        {runs.map((run) => <tr key={run.id}><td><strong>{run.name}</strong><small>{run.id}</small></td><td><StatusBadge value={run.status} /></td><td>{run.aggregate_score?.toFixed(3) ?? "—"}</td><td>{run.pass_threshold.toFixed(2)}</td><td>{run.agent_id || "—"}</td><td>{run.model_name || "—"}</td><td>{new Date(run.created_at).toLocaleString()}</td></tr>)}
      </tbody></table></div>
    </section>
  </>;
}
