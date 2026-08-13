"use client";

import { useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Budget = {
  tenant_id: string;
  period_key: string;
  monthly_token_limit: number;
  monthly_cost_limit_usd: number;
  used_tokens: number;
  used_cost_usd: number;
  allowed_providers: string[];
};

type Usage = {
  id: string;
  tenant_id: string;
  request_id?: string | null;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
  route_reason?: string | null;
  created_at: string;
};

export default function UsagePage() {
  const [tenantId, setTenantId] = useState("");
  const [budget, setBudget] = useState<Budget | null>(null);
  const [usage, setUsage] = useState<Usage[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function load() {
    if (!tenantId.trim()) return;
    setLoading(true);
    setError("");
    try {
      const encoded = encodeURIComponent(tenantId.trim());
      const [budgetData, usageData] = await Promise.all([
        redpaFetch<Budget>(`/api/v1/platform/v4/model-governance/${encoded}`, {}, true),
        redpaFetch<Usage[]>(`/api/v1/platform/v4/model-governance/${encoded}/usage?limit=200`, {}, true),
      ]);
      setBudget(budgetData);
      setUsage(usageData);
    } catch (err) {
      setBudget(null);
      setUsage([]);
      setError(err instanceof Error ? err.message : "Failed to load tenant usage");
    } finally {
      setLoading(false);
    }
  }

  const totals = useMemo(() => ({
    tokens: usage.reduce((sum, item) => sum + item.total_tokens, 0),
    cost: usage.reduce((sum, item) => sum + item.cost_usd, 0),
    providers: new Set(usage.map((item) => item.provider)).size,
  }), [usage]);

  return <>
    <header className="cpHeader"><div><p className="cpEyebrow">CONTROL PLANE / GOVERNANCE</p><h1>Usage & Cost</h1><p>Inspect tenant-scoped model budgets and persisted usage recorded by the model governance service.</p></div></header>
    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Tenant scope</span><h2>Load model governance</h2></div></div>
      <div className="cpFormRow"><input value={tenantId} onChange={(e) => setTenantId(e.target.value)} placeholder="Tenant UUID" /><button onClick={() => void load()} disabled={loading || !tenantId.trim()}>{loading ? "Loading…" : "Load usage"}</button></div>
      <p className="cpMuted">This view uses authenticated tenant-scoped V4 governance APIs. Store a valid access token as <code>redpa_access_token</code> in the browser session used by the existing frontend.</p>
    </section>
    {error ? <div className="cpNotice">{error}</div> : null}
    <section className="cpMetrics">
      <MetricCard label="Recorded requests" value={usage.length} />
      <MetricCard label="Usage tokens" value={totals.tokens.toLocaleString()} />
      <MetricCard label="Recorded cost" value={`$${totals.cost.toFixed(4)}`} />
      <MetricCard label="Providers used" value={totals.providers} />
    </section>

    {budget ? <section className="cpPanel">
      <div className="cpPanelHead"><div><span>{budget.period_key}</span><h2>Monthly budget</h2></div><StatusBadge value={budget.used_cost_usd <= budget.monthly_cost_limit_usd && budget.used_tokens <= budget.monthly_token_limit ? "within budget" : "limit exceeded"} /></div>
      <div className="cpDetailGrid">
        <div><span>Token budget</span><strong>{budget.used_tokens.toLocaleString()} / {budget.monthly_token_limit.toLocaleString()}</strong></div>
        <div><span>Cost budget</span><strong>${budget.used_cost_usd.toFixed(4)} / ${budget.monthly_cost_limit_usd.toFixed(2)}</strong></div>
        <div><span>Allowed providers</span><strong>{budget.allowed_providers.length ? budget.allowed_providers.join(", ") : "All configured"}</strong></div>
        <div><span>Tenant</span><strong>{budget.tenant_id}</strong></div>
      </div>
    </section> : null}

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Persisted accounting</span><h2>Recent model usage</h2></div></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Time</th><th>Provider</th><th>Model</th><th>Tokens</th><th>Cost</th><th>Route</th><th>Request</th></tr></thead><tbody>
        {usage.map((item) => <tr key={item.id}><td>{new Date(item.created_at).toLocaleString()}</td><td><StatusBadge value={item.provider} /></td><td>{item.model}</td><td>{item.total_tokens.toLocaleString()}<small>{item.input_tokens} in / {item.output_tokens} out</small></td><td>${item.cost_usd.toFixed(6)}</td><td>{item.route_reason || "—"}</td><td>{item.request_id || "—"}</td></tr>)}
      </tbody></table></div>
      {!usage.length ? <p className="cpMuted">Enter a tenant UUID to load recorded usage.</p> : null}
    </section>
  </>;
}
