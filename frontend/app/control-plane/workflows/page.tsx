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
  approval_required: boolean;
  approval_granted: boolean;
  review_reason?: string | null;
  max_parallelism: number;
  timeout_seconds: number;
  aggregated_response?: string | null;
  successful_subtasks: number;
  failed_subtasks: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  subtasks: Subtask[];
};

type ExecutionResponse = { workflow: Workflow; resumed: boolean; executed_subtasks: unknown[] };

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selected, setSelected] = useState<Workflow | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [resuming, setResuming] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const items = await redpaFetch<Workflow[]>("/api/v1/agents/distributed/durable?limit=100");
      setWorkflows(items);
      if (selected) {
        const refreshed = items.find((item) => item.id === selected.id);
        if (refreshed) setSelected(refreshed);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load durable workflows");
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
      setError(err instanceof Error ? err.message : "Failed to inspect workflow");
    }
  }

  async function resume(workflow: Workflow) {
    setResuming(workflow.id);
    setError("");
    setNotice("");
    try {
      const result = await redpaFetch<ExecutionResponse>(`/api/v1/agents/distributed/durable/${workflow.id}/resume`, {
        method: "POST",
        body: JSON.stringify({ approval_granted: workflow.approval_required, retry_failed: true, retry_running: true }),
      });
      setSelected(result.workflow);
      setNotice(`Workflow ${workflow.id} resumed successfully.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow resume failed");
    } finally {
      setResuming("");
    }
  }

  const counts = useMemo(() => ({
    completed: workflows.filter((item) => item.status.toLowerCase().includes("complete") || item.status.toLowerCase() === "succeeded").length,
    running: workflows.filter((item) => ["running", "in_progress", "executing"].includes(item.status.toLowerCase())).length,
    attention: workflows.filter((item) => item.failed_subtasks > 0 || item.approval_required && !item.approval_granted).length,
  }), [workflows]);

  return <>
    <header className="cpHeader"><div><p className="cpEyebrow">CONTROL PLANE / WORKFLOWS</p><h1>Durable Workflows</h1><p>Inspect persisted distributed workflows, subtask state and supported resume operations.</p></div><button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button></header>
    {notice ? <div className="cpSuccess">{notice}</div> : null}
    {error ? <div className="cpNotice">{error}</div> : null}
    <section className="cpMetrics"><MetricCard label="Workflows" value={workflows.length} /><MetricCard label="Completed" value={counts.completed} /><MetricCard label="Running" value={counts.running} /><MetricCard label="Needs attention" value={counts.attention} /></section>

    <section className="cpPanel"><div className="cpPanelHead"><div><span>Persistence</span><h2>Workflow history</h2></div></div><div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Workflow</th><th>Status</th><th>Subtasks</th><th>Approval</th><th>Updated</th><th></th></tr></thead><tbody>
      {workflows.map((workflow) => <tr key={workflow.id}><td><strong>{workflow.request}</strong><small>{workflow.id}</small></td><td><StatusBadge value={workflow.status} /></td><td>{workflow.successful_subtasks} ok / {workflow.failed_subtasks} failed</td><td>{workflow.approval_required ? (workflow.approval_granted ? "Granted" : "Required") : "Not required"}</td><td>{new Date(workflow.updated_at).toLocaleString()}</td><td><button className="cpLinkButton" onClick={() => void inspect(workflow.id)}>Inspect</button></td></tr>)}
    </tbody></table></div>{!workflows.length ? <p className="cpMuted">No durable workflows have been persisted yet.</p> : null}</section>

    {selected ? <section className="cpPanel"><div className="cpPanelHead"><div><span>Workflow detail</span><h2>{selected.request}</h2></div><StatusBadge value={selected.status} /></div>
      <div className="cpDetailGrid"><div><span>ID</span><strong>{selected.id}</strong></div><div><span>Parallelism</span><strong>{selected.max_parallelism}</strong></div><div><span>Timeout</span><strong>{selected.timeout_seconds}s</strong></div><div><span>Approval</span><strong>{selected.approval_required ? (selected.approval_granted ? "Granted" : "Required") : "Not required"}</strong></div></div>
      {selected.review_reason ? <div className="cpNotice"><strong>Review reason:</strong> {selected.review_reason}</div> : null}
      {selected.aggregated_response ? <div className="cpResponse"><span>Aggregated response</span><p>{selected.aggregated_response}</p></div> : null}
      <div className="cpPanelHead cpSubHead"><div><span>Execution</span><h2>Subtasks</h2></div><button onClick={() => void resume(selected)} disabled={resuming === selected.id}>{resuming === selected.id ? "Resuming…" : "Resume / retry"}</button></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Subtask</th><th>Status</th><th>Agent</th><th>Attempts</th><th>Latency</th><th>Result</th></tr></thead><tbody>{selected.subtasks.map((task) => <tr key={task.id}><td><strong>{task.subtask_key}</strong><small>{task.instruction}</small></td><td><StatusBadge value={task.status} /></td><td>{task.remote_agent || task.selected_skill || "—"}</td><td>{task.attempt_count}</td><td>{task.execution_time_ms.toFixed(1)} ms</td><td>{task.error || task.response || "—"}</td></tr>)}</tbody></table></div>
    </section> : null}
  </>;
}
