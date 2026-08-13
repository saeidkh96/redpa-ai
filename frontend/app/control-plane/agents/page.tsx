"use client";

import { FormEvent, useEffect, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Agent = { id: string; name: string; version: string; status: string; capability_names: string[]; supported_routes: string[] };
type AgentList = { items: Agent[]; total: number };
type AgentHealth = { status: string; total_agents: number; active_agents: number; degraded_agents: number; offline_agents: number };
type Match = { agent_id: string; agent_name: string; capability_name: string; capability_description: string; matched_tags: string[]; score: number };
type Search = { query: string; matches: Match[]; total: number };

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]); const [health, setHealth] = useState<AgentHealth | null>(null);
  const [query, setQuery] = useState(""); const [matches, setMatches] = useState<Match[]>([]); const [error, setError] = useState("");
  async function load() { setError(""); try { const [list, snapshot] = await Promise.all([redpaFetch<AgentList>("/api/v1/agents"), redpaFetch<AgentHealth>("/api/v1/agents/health")]); setAgents(list.items); setHealth(snapshot); } catch (e) { setError(e instanceof Error ? e.message : "Failed to load agents"); } }
  useEffect(() => { void load(); }, []);
  async function discover(e: FormEvent) { e.preventDefault(); if (!query.trim()) { setMatches([]); return; } try { const result = await redpaFetch<Search>(`/api/v1/agents/discover?query=${encodeURIComponent(query)}&limit=20`); setMatches(result.matches); } catch (err) { setError(err instanceof Error ? err.message : "Discovery failed"); } }
  return <><header className="cpHeader"><div><p className="cpEyebrow">CONTROL PLANE / AGENTS</p><h1>Agent Registry</h1><p>Live registry and capability discovery backed by the existing A2A agent APIs.</p></div><button onClick={() => void load()}>Refresh</button></header>{error ? <div className="cpNotice">{error}</div> : null}
    <section className="cpMetrics"><MetricCard label="Registered" value={health?.total_agents ?? agents.length} /><MetricCard label="Active" value={health?.active_agents ?? "—"} /><MetricCard label="Degraded" value={health?.degraded_agents ?? "—"} /><MetricCard label="Offline" value={health?.offline_agents ?? "—"} /></section>
    <section className="cpPanel"><div className="cpPanelHead"><div><span>Discovery</span><h2>Search by capability</h2></div></div><form className="cpSearch" onSubmit={discover}><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. postgres, research, filesystem" /><button>Discover</button></form>{matches.length ? <div className="cpResultGrid">{matches.map((m) => <article key={`${m.agent_id}-${m.capability_name}`}><div className="cpRow"><strong>{m.agent_name}</strong><b>{m.score.toFixed(2)}</b></div><h3>{m.capability_name}</h3><p>{m.capability_description}</p><div className="cpTags">{m.matched_tags.map((t) => <span key={t}>{t}</span>)}</div></article>)}</div> : null}</section>
    <section className="cpPanel"><div className="cpPanelHead"><div><span>Registry</span><h2>Registered agents</h2></div><StatusBadge value={health?.status} /></div><div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Agent</th><th>Status</th><th>Version</th><th>Capabilities</th><th>Routes</th></tr></thead><tbody>{agents.map((a) => <tr key={a.id}><td><strong>{a.name}</strong><small>{a.id}</small></td><td><StatusBadge value={a.status} /></td><td>{a.version}</td><td><div className="cpTags">{a.capability_names.map((c) => <span key={c}>{c}</span>)}</div></td><td><div className="cpTags">{a.supported_routes.map((r) => <span key={r}>{r}</span>)}</div></td></tr>)}</tbody></table></div></section></>;
}
