"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type RunEvent = {
  id: string;
  event_type: string;
  stage?: string | null;
  payload: Record<string, unknown>;
  created_at: string;
};

type Run = {
  id: string;
  agent_id: string;
  workflow_id?: string | null;
  trace_id?: string | null;
  status: string;
  objective: string;
  model_name?: string | null;
  evaluation_run_id?: string | null;
  evaluation_score?: number | null;
  error?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  events: RunEvent[];
};

type RunList = { items: Run[]; total: number; limit: number; offset: number };

export default function GovernancePage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selected, setSelected] = useState<Run | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const qs = statusFilter ? `?limit=100&status=${encodeURIComponent(statusFilter)}` : "?limit=100";
      const data = await redpaFetch<RunList>(`/api/v1/governance/v10/runs${qs}`, {}, true);
      setRuns(data.items);
      if (selected) {
        const fresh = data.items.find((run) => run.id === selected.id);
        if (fresh) setSelected(fresh);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load governed runs.");
    } finally {
      setLoading(false);
    }
  }

  async function openRun(id: string) {
    try {
      setSelected(await redpaFetch<Run>(`/api/v1/governance/v10/runs/${id}`, {}, true));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load run detail.");
    }
  }

  useEffect(() => { void load(); }, [statusFilter]);

  const stats = useMemo(() => ({
    running: runs.filter((r) => r.status === "running").length,
    blocked: runs.filter((r) => r.status === "blocked").length,
    completed: runs.filter((r) => r.status === "completed").length,
    failed: runs.filter((r) => r.status === "failed").length,
  }), [runs]);

  return <>
    <header className="cpHeader">
      <div>
        <p className="cpEyebrow">V10.1 / GOVERNED RUNTIME</p>
        <h1>Governance Runs</h1>
        <p>Inspect governed agent lifecycles, policy decisions, approval blocks, traces, recovery events, and evaluation outcomes.</p>
      </div>
      <div className="cpActions">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="cpSelect">
          <option value="">All statuses</option>
          <option value="running">Running</option>
          <option value="blocked">Blocked</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        <button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
      </div>
    </header>

    {error ? <div className="cpNotice">{error}</div> : null}

    <section className="cpMetrics">
      <MetricCard label="Running" value={stats.running} />
      <MetricCard label="Blocked" value={stats.blocked} />
      <MetricCard label="Completed" value={stats.completed} />
      <MetricCard label="Failed" value={stats.failed} />
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Persisted runtime</span><h2>Governed runs</h2></div><span>{runs.length} loaded</span></div>
      <div className="cpTableWrap">
        <table className="cpTable">
          <thead><tr><th>Created</th><th>Agent</th><th>Objective</th><th>Status</th><th>Evaluation</th><th>Trace</th><th></th></tr></thead>
          <tbody>
            {runs.map((run) => <tr key={run.id}>
              <td>{new Date(run.created_at).toLocaleString()}</td>
              <td><strong>{run.agent_id}</strong><small>{run.workflow_id || "—"}</small></td>
              <td className="cpObjective">{run.objective}</td>
              <td><StatusBadge value={run.status} /></td>
              <td>{run.evaluation_score ?? "—"}</td>
              <td><code className="cpCode">{run.trace_id?.slice(0, 12) || "—"}</code></td>
              <td><button className="cpLinkButton" onClick={() => void openRun(run.id)}>Inspect</button></td>
            </tr>)}
          </tbody>
        </table>
      </div>
      {!runs.length && !loading ? <p className="cpMuted">No governed runs match this filter.</p> : null}
    </section>

    {selected ? <section className="cpPanel">
      <div className="cpPanelHead">
        <div><span>Run detail</span><h2>{selected.agent_id}</h2></div>
        <StatusBadge value={selected.status} />
      </div>

      <div className="cpDetailGrid">
        <div><span>Run ID</span><strong>{selected.id}</strong></div>
        <div><span>Trace ID</span><strong>{selected.trace_id || "—"}</strong></div>
        <div><span>Evaluation</span><strong>{selected.evaluation_score ?? "—"}</strong></div>
        <div><span>Model</span><strong>{selected.model_name || "—"}</strong></div>
      </div>

      <div className="cpResponse">
        <span>Objective</span>
        <p>{selected.objective}</p>
        {selected.error ? <p className="cpRunError">{selected.error}</p> : null}
      </div>

      <div className="cpPanelHead cpSubHead"><div><span>Execution evidence</span><h2>Event timeline</h2></div><span>{selected.events.length} events</span></div>
      <div className="cpTimeline">
        {[...selected.events].sort((a,b) => +new Date(a.created_at) - +new Date(b.created_at)).map((event) =>
          <article key={event.id}>
            <span className="cpTimelineDot" />
            <div>
              <div className="cpTimelineTitle"><strong>{event.event_type}</strong><StatusBadge value={event.stage || "runtime"} /></div>
              <small>{new Date(event.created_at).toLocaleString()}</small>
              {Object.keys(event.payload || {}).length ? <pre>{JSON.stringify(event.payload, null, 2)}</pre> : null}
            </div>
          </article>
        )}
      </div>
    </section> : null}
  </>;
}
