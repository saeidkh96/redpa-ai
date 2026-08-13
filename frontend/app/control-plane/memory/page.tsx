"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Analytics = {
  total_memories: number;
  active_memories: number;
  inactive_memories: number;
  average_importance: number;
  by_scope: Record<string, number>;
  by_kind: Record<string, number>;
  by_agent: Record<string, number>;
  by_embedding_status: Record<string, number>;
};

type MemoryRecord = {
  id: string;
  agent_id: string;
  content: string;
  scope: string;
  kind: string;
  importance: number;
  is_active: boolean;
  embedding_status: string;
  created_at: string;
};

type SearchResult = {
  memory: MemoryRecord;
  score: number;
  semantic_score: number;
  importance_score: number;
  recency_score: number;
};

export default function MemoryPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [query, setQuery] = useState("");
  const [agentId, setAgentId] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setAnalytics(await redpaFetch<Analytics>("/api/v1/memory/admin/analytics"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load memory analytics");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  async function search() {
    if (!query.trim()) return;
    setSearching(true);
    setError("");
    try {
      const body: Record<string, unknown> = { query: query.trim(), limit: 20, include_shared: true };
      if (agentId.trim()) body.agent_id = agentId.trim();
      setResults(await redpaFetch<SearchResult[]>("/api/v1/memory/search", { method: "POST", body: JSON.stringify(body) }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Memory search failed");
    } finally {
      setSearching(false);
    }
  }

  const topAgents = useMemo(() => Object.entries(analytics?.by_agent || {}).sort((a,b) => b[1]-a[1]).slice(0,10), [analytics]);

  return <>
    <header className="cpHeader"><div><p className="cpEyebrow">CONTROL PLANE / MEMORY</p><h1>Agent Memory</h1><p>Inspect real memory analytics and run semantic searches against the implemented memory service.</p></div><button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button></header>
    {error ? <div className="cpNotice">{error}</div> : null}
    <section className="cpMetrics">
      <MetricCard label="Total memories" value={analytics?.total_memories ?? "—"} />
      <MetricCard label="Active" value={analytics?.active_memories ?? "—"} />
      <MetricCard label="Inactive" value={analytics?.inactive_memories ?? "—"} />
      <MetricCard label="Avg importance" value={analytics ? analytics.average_importance.toFixed(3) : "—"} />
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Semantic retrieval</span><h2>Search memory</h2></div></div>
      <div className="cpFormRow">
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search memory content…" />
        <input value={agentId} onChange={(e) => setAgentId(e.target.value)} placeholder="Agent ID (optional)" />
        <button onClick={() => void search()} disabled={searching || !query.trim()}>{searching ? "Searching…" : "Search"}</button>
      </div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Memory</th><th>Agent</th><th>Scope</th><th>Kind</th><th>Embedding</th><th>Score</th></tr></thead><tbody>
        {results.map(({memory, score}) => <tr key={memory.id}><td><strong>{memory.content}</strong><small>{memory.id}</small></td><td>{memory.agent_id}</td><td><StatusBadge value={memory.scope} /></td><td>{memory.kind}</td><td><StatusBadge value={memory.embedding_status} /></td><td>{score.toFixed(3)}</td></tr>)}
      </tbody></table></div>
      {!results.length ? <p className="cpMuted">Run a semantic search to inspect matching memories.</p> : null}
    </section>

    <section className="cpGrid2">
      <div className="cpPanel"><div className="cpPanelHead"><div><span>Distribution</span><h2>Scopes</h2></div></div>{Object.entries(analytics?.by_scope || {}).map(([key,value]) => <div className="cpListRow" key={key}><StatusBadge value={key} /><strong>{value}</strong></div>)}</div>
      <div className="cpPanel"><div className="cpPanelHead"><div><span>Distribution</span><h2>Top agents</h2></div></div>{topAgents.map(([key,value]) => <div className="cpListRow" key={key}><span>{key}</span><strong>{value}</strong></div>)}</div>
    </section>
  </>;
}
