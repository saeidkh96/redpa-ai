"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Dependency = { name: string; status: string; latency_ms?: number };
type Health = { status: string; service?: string; version?: string; environment?: string; dependencies?: Dependency[] };
type AgentHealth = { status: string; total_agents: number; active_agents: number; degraded_agents: number; offline_agents: number };
type Provider = { name: string; provider_type: string; default_model: string; capabilities: string[]; enabled: boolean };
type ProviderHealth = { provider: string; available: boolean; models: string[]; detail?: string | null };

export default function ControlPlaneOverview() {
  const [health, setHealth] = useState<Health | null>(null);
  const [agentHealth, setAgentHealth] = useState<AgentHealth | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [providerHealth, setProviderHealth] = useState<ProviderHealth[]>([]);
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true); setNotice("");
    const [h, a, p, ph] = await Promise.allSettled([
      redpaFetch<Health>("/api/v1/platform/health"),
      redpaFetch<AgentHealth>("/api/v1/agents/health"),
      redpaFetch<Provider[]>("/api/v1/model-gateway/providers", {}, true),
      redpaFetch<ProviderHealth[]>("/api/v1/model-gateway/health", {}, true),
    ]);
    if (h.status === "fulfilled") setHealth(h.value);
    if (a.status === "fulfilled") setAgentHealth(a.value);
    if (p.status === "fulfilled") setProviders(p.value);
    if (ph.status === "fulfilled") setProviderHealth(ph.value);
    const failures = [h, a, p, ph].filter((r) => r.status === "rejected");
    if (failures.length) setNotice("Some protected Model Gateway data requires a valid RedPA access token. Public platform and agent health remain available.");
    setLoading(false);
  }

  useEffect(() => { void load(); }, []);

  const availableProviders = useMemo(() => providerHealth.filter((item) => item.available).length, [providerHealth]);

  return <>
    <header className="cpHeader">
      <div><p className="cpEyebrow">REDPA AI · V5</p><h1>Control Plane</h1><p>Operational view over the APIs already implemented by the RedPA platform.</p></div>
      <button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
    </header>
    {notice ? <div className="cpNotice">{notice}</div> : null}
    <section className="cpMetrics">
      <MetricCard label="Platform" value={health?.status || "unknown"} hint={health?.version ? `version ${health.version}` : "deep health"} />
      <MetricCard label="Registered agents" value={agentHealth?.total_agents ?? "—"} hint={`${agentHealth?.active_agents ?? 0} active`} />
      <MetricCard label="Model providers" value={providers.length || "—"} hint={providers.length ? `${availableProviders} available` : "sign in for provider data"} />
      <MetricCard label="Dependencies" value={health?.dependencies?.length ?? "—"} hint={health?.environment || "runtime services"} />
    </section>
    <section className="cpGrid2">
      <div className="cpPanel"><div className="cpPanelHead"><div><span>Runtime</span><h2>Platform dependencies</h2></div><StatusBadge value={health?.status} /></div>
        <div className="cpRows">{health?.dependencies?.length ? health.dependencies.map((dep) => <div className="cpRow" key={dep.name}><div><strong>{dep.name}</strong><small>{dep.latency_ms != null ? `${dep.latency_ms} ms` : "dependency"}</small></div><StatusBadge value={dep.status} /></div>) : <p className="cpMuted">No dependency snapshot available.</p>}</div>
      </div>
      <div className="cpPanel"><div className="cpPanelHead"><div><span>Gateway</span><h2>Provider health</h2></div><Link href="/control-plane/models">Open models →</Link></div>
        <div className="cpRows">{providerHealth.length ? providerHealth.map((item) => <div className="cpRow" key={item.provider}><div><strong>{item.provider}</strong><small>{item.models.length} reported model(s)</small></div><StatusBadge value={item.available ? "available" : "unavailable"} /></div>) : <p className="cpMuted">Authenticate to inspect protected provider health.</p>}</div>
      </div>
    </section>
    <section className="cpPanel"><div className="cpPanelHead"><div><span>Navigate</span><h2>Control Plane surfaces</h2></div></div>
      <div className="cpLaunchGrid"><Link href="/control-plane/agents"><strong>Agents</strong><span>Registry, health and capability discovery</span></Link><Link href="/control-plane/models"><strong>Models</strong><span>Providers, models, health and circuits</span></Link><Link href="/evaluations"><strong>Evaluations</strong><span>Existing evaluation dashboard</span></Link><Link href="/policy"><strong>Governance</strong><span>Existing policy control center</span></Link></div>
    </section>
  </>;
}
