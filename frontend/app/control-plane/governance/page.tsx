"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type AuditEvent = {
  id: string;
  boundary: string;
  action: string;
  resource?: string | null;
  decision: string;
  risk: string;
  reason: string;
  matched_rules: string[];
  policy_version: string;
  source: string;
  review_id?: string | null;
  created_at: string;
};

type Enforcement = {
  decision: string;
  risk: string;
  reason: string;
  matched_rules: string[];
  policy_version: string;
  source: string;
  executable: boolean;
  review_id?: string | null;
};

export default function GovernancePage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [boundary, setBoundary] = useState("mcp");
  const [action, setAction] = useState("list_containers");
  const [resource, setResource] = useState("mcp_tool");
  const [argumentsText, setArgumentsText] = useState("{}");
  const [result, setResult] = useState<Enforcement | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setEvents(await redpaFetch<AuditEvent[]>("/api/v1/policy/audit?limit=200", {}, true));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load policy audit");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  async function evaluate() {
    setEvaluating(true);
    setError("");
    setResult(null);
    try {
      const parsed = JSON.parse(argumentsText || "{}");
      const response = await redpaFetch<Enforcement>("/api/v1/policy/enforce", {
        method: "POST",
        body: JSON.stringify({ boundary, action, resource, arguments: parsed }),
      }, true);
      setResult(response);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Policy evaluation failed");
    } finally {
      setEvaluating(false);
    }
  }

  const stats = useMemo(() => ({
    allow: events.filter((e) => e.decision === "ALLOW").length,
    review: events.filter((e) => e.decision === "REVIEW").length,
    deny: events.filter((e) => e.decision === "DENY").length,
    critical: events.filter((e) => e.risk === "CRITICAL").length,
  }), [events]);

  return <>
    <header className="cpHeader">
      <div><p className="cpEyebrow">CONTROL PLANE / GOVERNANCE</p><h1>Policy & Audit</h1><p>Evaluate actions against the implemented policy boundary and inspect the persisted audit trail.</p></div>
      <button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
    </header>

    {error ? <div className="cpNotice">{error}</div> : null}

    <section className="cpMetrics">
      <MetricCard label="Audit events" value={events.length} />
      <MetricCard label="Allowed" value={stats.allow} />
      <MetricCard label="Review" value={stats.review} />
      <MetricCard label="Denied / critical" value={`${stats.deny} / ${stats.critical}`} />
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Live policy engine</span><h2>Enforcement preview</h2></div></div>
      <div className="cpGovernanceForm">
        <label><span>Action</span><input value={action} onChange={(e) => setAction(e.target.value)} /></label>
        <label><span>Boundary</span><select value={boundary} onChange={(e) => setBoundary(e.target.value)}><option value="mcp">MCP</option><option value="internal_tool">Internal tool</option><option value="workflow">Workflow</option></select></label>
        <label><span>Resource</span><input value={resource} onChange={(e) => setResource(e.target.value)} /></label>
        <label className="wide"><span>Arguments JSON</span><textarea value={argumentsText} rows={5} onChange={(e) => setArgumentsText(e.target.value)} /></label>
      </div>
      <div className="cpActions"><button onClick={() => void evaluate()} disabled={evaluating}>{evaluating ? "Evaluating…" : "Evaluate policy"}</button></div>

      {result ? <div className="cpResponse cpResultPanel">
        <span>Policy result</span>
        <div className="cpResultSummary"><StatusBadge value={result.decision} /><StatusBadge value={result.risk} /><strong>{result.executable ? "Executable" : "Blocked"}</strong></div>
        <p>{result.reason}</p>
        <small>{result.matched_rules.length ? `Matched: ${result.matched_rules.join(", ")}` : "No matched rule"} · {result.policy_version} · {result.source}</small>
        {result.review_id ? <small>Human review: {result.review_id}</small> : null}
      </div> : null}
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Persisted audit</span><h2>Policy events</h2></div></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Time</th><th>Action</th><th>Decision</th><th>Risk</th><th>Boundary</th><th>Rules</th><th>Review</th></tr></thead><tbody>
        {events.map((event) => <tr key={event.id}><td>{new Date(event.created_at).toLocaleString()}</td><td><strong>{event.action}</strong><small>{event.resource || "—"}</small></td><td><StatusBadge value={event.decision} /></td><td><StatusBadge value={event.risk} /></td><td>{event.boundary}</td><td>{event.matched_rules.join(", ") || "—"}</td><td>{event.review_id || "—"}</td></tr>)}
      </tbody></table></div>
      {!events.length ? <p className="cpMuted">No policy audit events are available for the current user.</p> : null}
    </section>
  </>;
}
