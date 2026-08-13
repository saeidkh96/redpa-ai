"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Subtask = {
  id: string;
  subtask_key: string;
  instruction: string;
  status: string;
  remote_agent?: string | null;
  selected_skill?: string | null;
  response?: string | null;
  execution_time_ms: number;
  error?: string | null;
  attempt_count: number;
};

type Workflow = {
  id: string;
  request: string;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  successful_subtasks: number;
  failed_subtasks: number;
  subtasks: Subtask[];
};

export default function ExecutionsPage() {
  const [runs, setRuns] = useState<Workflow[]>([]);
  const [selected, setSelected] = useState<Workflow | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await redpaFetch<Workflow[]>("/api/v1/agents/distributed/durable?limit=100");
      setRuns(data);
      if (selected) {
        const current = data.find((item) => item.id === selected.id);
        if (current) setSelected(current);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load executions");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  async function inspect(id: string) {
    setError("");
    try {
      setSelected(await redpaFetch<Workflow>(`/api/v1/agents/distributed/durable/${id}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to inspect execution");
    }
  }

  const stats = useMemo(() => {
    const subtasks = runs.flatMap((run) => run.subtasks || []);
    const latency = subtasks.reduce((sum, item) => sum + (item.execution_time_ms || 0), 0);
    return {
      subtasks: subtasks.length,
      failures: subtasks.filter((item) => item.error || item.status.toLowerCase().includes("fail")).length,
      avgLatency: subtasks.length ? latency / subtasks.length : 0,
    };
  }, [runs]);

  return <>
    <header className="cpHeader">
      <div><p className="cpEyebrow">CONTROL PLANE / EXECUTIONS</p><h1>Execution Explorer</h1><p>Inspect persisted distributed-agent executions and their real subtask timing, attempts, routing and outcomes.</p></div>
      <button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
    </header>
    {error ? <div className="cpNotice">{error}</div> : null}
    <section className="cpMetrics">
      <MetricCard label="Persisted runs" value={runs.length} />
      <MetricCard label="Subtasks" value={stats.subtasks} />
      <MetricCard label="Failures" value={stats.failures} />
      <MetricCard label="Avg subtask latency" value={`${stats.avgLatency.toFixed(1)} ms`} />
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Runtime history</span><h2>Distributed executions</h2></div></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Request</th><th>Status</th><th>Success</th><th>Failed</th><th>Updated</th><th></th></tr></thead><tbody>
        {runs.map((run) => <tr key={run.id}><td><strong>{run.request}</strong><small>{run.id}</small></td><td><StatusBadge value={run.status} /></td><td>{run.successful_subtasks}</td><td>{run.failed_subtasks}</td><td>{new Date(run.updated_at).toLocaleString()}</td><td><button className="cpLinkButton" onClick={() => void inspect(run.id)}>Trace</button></td></tr>)}
      </tbody></table></div>
      {!runs.length ? <p className="cpMuted">No persisted distributed executions are available yet.</p> : null}
    </section>

    {selected ? <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Execution trace</span><h2>{selected.request}</h2></div><StatusBadge value={selected.status} /></div>
      <div className="cpDetailGrid">
        <div><span>Execution ID</span><strong>{selected.id}</strong></div>
        <div><span>Created</span><strong>{new Date(selected.created_at).toLocaleString()}</strong></div>
        <div><span>Updated</span><strong>{new Date(selected.updated_at).toLocaleString()}</strong></div>
        <div><span>Completed</span><strong>{selected.completed_at ? new Date(selected.completed_at).toLocaleString() : "—"}</strong></div>
      </div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Step</th><th>Status</th><th>Route</th><th>Attempts</th><th>Latency</th><th>Outcome</th></tr></thead><tbody>
        {selected.subtasks.map((task) => <tr key={task.id}><td><strong>{task.subtask_key}</strong><small>{task.instruction}</small></td><td><StatusBadge value={task.status} /></td><td>{task.remote_agent || task.selected_skill || "—"}</td><td>{task.attempt_count}</td><td>{task.execution_time_ms.toFixed(1)} ms</td><td>{task.error || task.response || "—"}</td></tr>)}
      </tbody></table></div>
      {Object.keys(selected.metadata || {}).length ? <div className="cpResponse"><span>Execution metadata</span><pre>{JSON.stringify(selected.metadata, null, 2)}</pre></div> : null}
    </section> : null}
  </>;
}
