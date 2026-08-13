"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Provider = { name: string; provider_type: string; default_model: string; capabilities: string[]; enabled: boolean };
type Health = { provider: string; available: boolean; models: string[]; detail?: string | null };
type Circuit = { provider: string; state: string; failures: number; failure_threshold: number; recovery_timeout_seconds: number };

export default function ModelsPage() {
  const [providers, setProviders] = useState<Provider[]>([]); const [health, setHealth] = useState<Health[]>([]); const [circuits, setCircuits] = useState<Circuit[]>([]); const [notice, setNotice] = useState("");
  async function load() { setNotice(""); try { const [p,h,c] = await Promise.all([redpaFetch<Provider[]>("/api/v1/model-gateway/providers", {}, true), redpaFetch<Health[]>("/api/v1/model-gateway/health", {}, true), redpaFetch<Circuit[]>("/api/v1/model-gateway/circuits", {}, true)]); setProviders(p); setHealth(h); setCircuits(c); } catch(e) { setNotice(e instanceof Error ? e.message : "Unable to load model gateway"); } }
  useEffect(() => { void load(); }, []);
  const available = useMemo(() => health.filter((h) => h.available).length, [health]); const models = useMemo(() => new Set(health.flatMap((h) => h.models)).size, [health]);
  return <><header className="cpHeader"><div><p className="cpEyebrow">CONTROL PLANE / MODELS</p><h1>Models & Providers</h1><p>Read-only operational view over the implemented Model Gateway provider registry, health checks and circuit breakers.</p></div><button onClick={() => void load()}>Refresh</button></header>{notice ? <div className="cpNotice">{notice}. Sign in from the existing RedPA Control Center if authentication is required.</div> : null}
    <section className="cpMetrics"><MetricCard label="Providers" value={providers.length || "—"} /><MetricCard label="Available" value={health.length ? available : "—"} /><MetricCard label="Reported models" value={health.length ? models : "—"} /><MetricCard label="Circuit breakers" value={circuits.length || "—"} /></section>
    <section className="cpGrid2"><div className="cpPanel"><div className="cpPanelHead"><div><span>Registry</span><h2>Configured providers</h2></div></div><div className="cpRows">{providers.map((p) => { const h=health.find((x)=>x.provider===p.name); return <div className="cpProvider" key={p.name}><div className="cpRow"><div><strong>{p.name}</strong><small>{p.provider_type} · default {p.default_model}</small></div><StatusBadge value={h ? (h.available ? "available" : "unavailable") : (p.enabled ? "active" : "offline")} /></div><div className="cpTags">{p.capabilities.map((c)=><span key={c}>{c}</span>)}</div>{h?.detail ? <p>{h.detail}</p> : null}</div>;})}{!providers.length ? <p className="cpMuted">No authenticated provider data loaded.</p> : null}</div></div>
      <div className="cpPanel"><div className="cpPanelHead"><div><span>Reliability</span><h2>Circuit breakers</h2></div></div><div className="cpRows">{circuits.map((c)=><div className="cpCircuit" key={c.provider}><div className="cpRow"><strong>{c.provider}</strong><StatusBadge value={c.state} /></div><div className="cpCircuitMeta"><span>Failures <b>{c.failures}/{c.failure_threshold}</b></span><span>Recovery <b>{c.recovery_timeout_seconds}s</b></span></div></div>)}{!circuits.length ? <p className="cpMuted">No circuit snapshot loaded.</p> : null}</div></div></section>
    <section className="cpPanel"><div className="cpPanelHead"><div><span>Models</span><h2>Models reported by provider health</h2></div></div><div className="cpModelGrid">{health.map((h)=><article key={h.provider}><div className="cpRow"><strong>{h.provider}</strong><StatusBadge value={h.available ? "available" : "unavailable"} /></div><div className="cpTags">{h.models.length ? h.models.map((m)=><span key={m}>{m}</span>) : <span>no models reported</span>}</div></article>)}</div></section></>;
}
