"use client";

import { useEffect, useState } from "react";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Override = {
  id: string;
  action: string;
  boundary: string;
  resource?: string | null;
  decision: string;
  risk: string;
  reason: string;
  enabled: boolean;
  updated_at: string;
};

type Enforcement = {
  decision: string;
  risk: string;
  reason: string;
  matched_rules: string[];
  policy_version: string;
  source: string;
  executable: boolean;
};

export default function PolicyManagementPage() {
  const [items, setItems] = useState<Override[]>([]);
  const [action, setAction] = useState("restart_container");
  const [boundary, setBoundary] = useState("ops_remediation");
  const [decision, setDecision] = useState("REVIEW");
  const [risk, setRisk] = useState("HIGH");
  const [reason, setReason] = useState("Operational restart requires explicit human approval.");
  const [preview, setPreview] = useState<Enforcement | null>(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      setItems(await redpaFetch<Override[]>("/api/v1/policy/overrides", {}, true));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load policy overrides.");
    }
  }

  useEffect(() => { void load(); }, []);

  async function create() {
    setError("");
    try {
      await redpaFetch("/api/v1/policy/overrides", {
        method: "POST",
        body: JSON.stringify({ action, boundary, decision, risk, reason, enabled: true }),
      }, true);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create policy override.");
    }
  }

  async function toggle(item: Override) {
    await redpaFetch(`/api/v1/policy/overrides/${item.id}`, {
      method: "PATCH",
      body: JSON.stringify({ enabled: !item.enabled }),
    }, true);
    await load();
  }

  async function remove(id: string) {
    await redpaFetch(`/api/v1/policy/overrides/${id}`, { method: "DELETE" }, true);
    await load();
  }

  async function evaluate() {
    setError("");
    try {
      setPreview(await redpaFetch<Enforcement>("/api/v1/policy/enforce", {
        method: "POST",
        body: JSON.stringify({ action, boundary, arguments: {}, approval_granted: false }),
      }, true));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Policy preview failed.");
    }
  }

  return <>
    <header className="cpHeader">
      <div>
        <p className="cpEyebrow">V10.2 / POLICY MANAGEMENT</p>
        <h1>Operation Policy</h1>
        <p>Tune per-operation governance thresholds with persisted user-scoped ALLOW, REVIEW, and DENY overrides.</p>
      </div>
      <button onClick={() => void load()}>Refresh</button>
    </header>

    {error ? <div className="cpNotice">{error}</div> : null}

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Policy override</span><h2>Create operation rule</h2></div></div>
      <div className="cpPolicyGrid">
        <label><span>Action</span><input value={action} onChange={(e) => setAction(e.target.value)} /></label>
        <label><span>Boundary</span><input value={boundary} onChange={(e) => setBoundary(e.target.value)} /></label>
        <label><span>Decision</span><select value={decision} onChange={(e) => setDecision(e.target.value)}><option>ALLOW</option><option>REVIEW</option><option>DENY</option></select></label>
        <label><span>Risk</span><select value={risk} onChange={(e) => setRisk(e.target.value)}><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>CRITICAL</option></select></label>
        <label className="wide"><span>Reason</span><textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} /></label>
      </div>
      <div className="cpActions">
        <button onClick={() => void create()}>Save override</button>
        <button className="cpSecondary" onClick={() => void evaluate()}>Preview current action</button>
      </div>
      {preview ? <div className="cpResponse cpResultPanel">
        <span>Effective decision</span>
        <div className="cpResultSummary"><StatusBadge value={preview.decision} /><StatusBadge value={preview.risk} /><strong>{preview.executable ? "Executable" : "Approval / block"}</strong></div>
        <p>{preview.reason}</p>
        <small>{preview.source} · policy {preview.policy_version}</small>
      </div> : null}
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>User-scoped runtime policy</span><h2>Overrides</h2></div><span>{items.length} rules</span></div>
      <div className="cpTableWrap"><table className="cpTable">
        <thead><tr><th>Action</th><th>Boundary</th><th>Decision</th><th>Risk</th><th>State</th><th>Reason</th><th></th></tr></thead>
        <tbody>{items.map((item) => <tr key={item.id}>
          <td><strong>{item.action}</strong></td>
          <td>{item.boundary}</td>
          <td><StatusBadge value={item.decision} /></td>
          <td><StatusBadge value={item.risk} /></td>
          <td><StatusBadge value={item.enabled ? "active" : "disabled"} /></td>
          <td className="cpObjective">{item.reason}</td>
          <td><div className="cpActions"><button className="cpSecondary" onClick={() => void toggle(item)}>{item.enabled ? "Disable" : "Enable"}</button><button className="cpDanger" onClick={() => void remove(item.id)}>Delete</button></div></td>
        </tr>)}</tbody>
      </table></div>
      {!items.length ? <p className="cpMuted">No overrides configured. The external Policy Service remains authoritative.</p> : null}
    </section>
  </>;
}
