"use client";

import { useEffect, useMemo, useState } from "react";

type RecordItem = {
  id: string;
  version: number;
  kind: string;
  status: string;
  summary: string;
  created_at: string;
};

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const milestones = [
  [11, "Autonomous Reliability", "Closed-loop reliability decisions backed by persisted evidence."],
  [12, "Self-Healing Multi-Agent", "Health-aware failover and safe specialist rerouting."],
  [13, "Adaptive Governance", "Policy recommendations from operational risk signals; never auto-applied."],
  [14, "Security & Compliance", "Structured compliance evidence and completeness checks."],
  [15, "Production Cloud", "Deployment-readiness scoring for production controls."],
  [16, "Continuous Improvement", "Candidate-vs-baseline rollout decisions and regression protection."],
  [17, "Enterprise Integration", "Risk assessment for connectors and side-effect boundaries."],
  [18, "Trusted Agent Registry", "Versioned agent registration with trust-state requirements."],
] as const;

function token() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("redpa_access_token") ?? "";
}

export default function EvolutionPage() {
  const [items, setItems] = useState<RecordItem[]>([]);
  const [error, setError] = useState("");

  async function refresh() {
    setError("");
    const response = await fetch(`${API}/platform/evolution/records`, {
      headers: { Authorization: `Bearer ${token()}` },
      cache: "no-store",
    });
    if (!response.ok) {
      setError((await response.text()) || `HTTP ${response.status}`);
      return;
    }
    const data = await response.json();
    setItems(data.items ?? []);
  }

  useEffect(() => { void refresh(); }, []);

  const counts = useMemo(() => {
    const result: Record<number, number> = {};
    for (const item of items) result[item.version] = (result[item.version] ?? 0) + 1;
    return result;
  }, [items]);

  return (
    <div className="cpPage">
      <div className="cpEyebrow">V11-V18 / PLATFORM EVOLUTION</div>
      <div className="cpPageHeader">
        <div>
          <h1>Autonomous Platform Roadmap</h1>
          <p>Operational evidence for reliability, failover, adaptive governance, compliance, cloud readiness, continuous evaluation, integrations, and agent trust.</p>
        </div>
        <button className="cpButton" onClick={() => void refresh()}>Refresh</button>
      </div>

      {error ? <div className="cpNotice cpNoticeDanger">{error}</div> : null}

      <div className="cpCardGrid">
        {milestones.map(([version, name, description]) => (
          <section className="cpCard" key={version}>
            <div className="cpEyebrow">V{version}</div>
            <h2>{name}</h2>
            <p>{description}</p>
            <strong>{counts[version] ?? 0} persisted records</strong>
          </section>
        ))}
      </div>

      <section className="cpPanel">
        <div className="cpPanelHeader">
          <div><div className="cpEyebrow">PERSISTED EVIDENCE</div><h2>Evolution records</h2></div>
          <span>{items.length} loaded</span>
        </div>
        <div className="cpTableWrap">
          <table className="cpTable">
            <thead><tr><th>Created</th><th>Version</th><th>Kind</th><th>Status</th><th>Summary</th></tr></thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                  <td><strong>V{item.version}</strong></td>
                  <td>{item.kind}</td>
                  <td><strong>{item.status}</strong></td>
                  <td>{item.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!items.length ? <p className="cpEmpty">No V11-V18 evidence has been persisted yet.</p> : null}
        </div>
      </section>
    </div>
  );
}
