"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type WorkflowSubtask = {
  id: string;
  subtask_key: string;
  instruction: string;
  status: string;
  remote_agent?: string | null;
  selected_skill?: string | null;
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
  aggregated_response?: string | null;
  successful_subtasks: number;
  failed_subtasks: number;
  created_at: string;
  subtasks: WorkflowSubtask[];
};

type Review = {
  id: string;
  status: string;
  reason: string;
  requested_action?: string | null;
  request_content?: string | null;
  reviewer_feedback?: string | null;
  created_at: string;
};

type ReviewList = { items: Review[]; total: number };

type Memory = {
  id: string;
  agent_id: string;
  content: string;
  scope: string;
  kind: string;
  importance: number;
  embedding_status: string;
  updated_at: string;
};

type MemorySearch = { memory: Memory; score: number };

type Health = {
  status: string;
  version?: string;
  environment?: string;
  dependencies?: { name: string; status: string; latency_ms?: number }[];
};

type AgentList = { items: { id: string; name: string; status: string; capability_names: string[] }[]; total: number };
type RemoteList = { items: { name: string; connected: boolean; agent_name?: string | null; skills: string[] }[]; total: number };
type TokenResponse = { access_token: string };

type CapabilitySearch = {
  matches: { agent_id: string; agent_name: string; capability_name: string; score: number }[];
};

const tone = (status?: string) => {
  const value = (status || "").toLowerCase();
  if (["healthy", "active", "completed", "approved", "connected"].includes(value)) return "ok";
  if (["running", "pending", "queued", "degraded", "paused"].includes(value)) return "warn";
  if (["failed", "rejected", "offline", "unhealthy"].includes(value)) return "bad";
  return "neutral";
};

const when = (value?: string) => value ? new Date(value).toLocaleString() : "—";

export default function Dashboard() {
  const api = process.env.NEXT_PUBLIC_REDPA_API_URL || "http://localhost:8000";
  const [health, setHealth] = useState<Health | null>(null);
  const [agents, setAgents] = useState<AgentList | null>(null);
  const [remotes, setRemotes] = useState<RemoteList | null>(null);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selected, setSelected] = useState<Workflow | null>(null);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [memoryResults, setMemoryResults] = useState<MemorySearch[]>([]);
  const [reviews, setReviews] = useState<ReviewList | null>(null);
  const [token, setToken] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [memoryQuery, setMemoryQuery] = useState("");
  const [memoryAgent, setMemoryAgent] = useState("");
  const [memoryScope, setMemoryScope] = useState("");
  const [memoryKind, setMemoryKind] = useState("");
  const [agentQuery, setAgentQuery] = useState("");
  const [agentMatches, setAgentMatches] = useState<CapabilitySearch | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("redpa_access_token");
    if (saved) setToken(saved);
  }, []);

  const request = useCallback(async <T,>(path: string, init?: RequestInit, auth = false): Promise<T> => {
    const headers = new Headers(init?.headers || {});
    if (auth && token) headers.set("Authorization", `Bearer ${token}`);
    const response = await fetch(`${api}${path}`, { ...init, headers, cache: "no-store" });
    if (!response.ok) {
      let detail = `${response.status} ${response.statusText}`;
      try { const body = await response.json(); detail = body.detail || detail; } catch {}
      throw new Error(detail);
    }
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }, [api, token]);

  const refresh = useCallback(async () => {
    const results = await Promise.allSettled([
      request<Health>("/api/v1/platform/health"),
      request<AgentList>("/api/v1/agents"),
      request<RemoteList>("/api/v1/agents/remotes"),
      request<Workflow[]>("/api/v1/agents/distributed/durable?limit=50"),
      request<Memory[]>("/api/v1/memory?limit=100"),
    ]);
    if (results[0].status === "fulfilled") setHealth(results[0].value);
    if (results[1].status === "fulfilled") setAgents(results[1].value);
    if (results[2].status === "fulfilled") setRemotes(results[2].value);
    if (results[3].status === "fulfilled") setWorkflows(results[3].value);
    if (results[4].status === "fulfilled") setMemories(results[4].value);
    const errors = results.filter(r => r.status === "rejected").map(r => r.status === "rejected" ? r.reason?.message : "");
    setMessage(errors.length ? errors.join(" · ") : null);
  }, [request]);

  const loadReviews = useCallback(async () => {
    if (!token) { setReviews(null); return; }
    try {
      setReviews(await request<ReviewList>("/api/v1/reviews?limit=100&offset=0", undefined, true));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load reviews");
    }
  }, [request, token]);

  useEffect(() => {
    void refresh();
    const id = setInterval(() => void refresh(), 15000);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => { void loadReviews(); }, [loadReviews]);

  const pendingReviews = reviews?.items.filter(r => r.status === "pending").length ?? 0;
  const connectedRemotes = remotes?.items.filter(r => r.connected).length ?? 0;
  const healthyDeps = health?.dependencies?.filter(d => d.status === "healthy").length ?? 0;
  const totalDeps = health?.dependencies?.length ?? 0;

  const login = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const form = new URLSearchParams({ username: email, password });
      const result = await request<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });
      localStorage.setItem("redpa_access_token", result.access_token);
      setToken(result.access_token);
      setPassword("");
      setMessage(null);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Login failed");
    }
  };

  const reviewAction = async (review: Review, action: "approve" | "reject" | "resume") => {
    try {
      await request(`/api/v1/reviews/${review.id}/${action}`, {
        method: "POST",
        headers: action === "resume" ? undefined : { "Content-Type": "application/json" },
        body: action === "resume" ? undefined : JSON.stringify({ feedback: feedback[review.id] || null }),
      }, true);
      await loadReviews();
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Review action failed");
    }
  };

  const searchMemory = async (event: FormEvent) => {
    event.preventDefault();
    if (!memoryQuery.trim()) { setMemoryResults([]); return; }
    const body: Record<string, unknown> = { query: memoryQuery.trim(), limit: 20, min_score: 0.2, include_shared: true };
    if (memoryAgent.trim()) body.agent_id = memoryAgent.trim();
    if (memoryScope) body.scopes = [memoryScope];
    if (memoryKind) body.kinds = [memoryKind];
    try {
      setMemoryResults(await request<MemorySearch[]>("/api/v1/memory/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Memory search failed");
    }
  };

  const deleteMemory = async (id: string) => {
    if (!confirm("Delete this memory permanently?")) return;
    try {
      await request<void>(`/api/v1/memory/${id}`, { method: "DELETE" });
      setMemoryResults(values => values.filter(item => item.memory.id !== id));
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Memory deletion failed");
    }
  };

  const discover = async (event: FormEvent) => {
    event.preventDefault();
    if (!agentQuery.trim()) { setAgentMatches(null); return; }
    try {
      setAgentMatches(await request<CapabilitySearch>(`/api/v1/agents/discover?query=${encodeURIComponent(agentQuery.trim())}&limit=8`));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Agent discovery failed");
    }
  };

  const memoryView = memoryResults.length ? memoryResults : memories.map(memory => ({ memory, score: -1 }));

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><img src="/logo.png" alt="RedPA AI" /><div><strong>RedPA AI</strong><span>Control Center</span></div></div>
        <nav>
          <a href="#overview">Overview</a><a href="#workflows">Workflows</a><a href="#reviews">Human Reviews</a><a href="#memory">Memory</a><a href="#agents">Agents</a>
        </nav>
        <div className="sidebarFooter"><span className={`dot ${health?.status === "healthy" ? "dotHealthy" : ""}`} /><div><strong>{health?.status || "Connecting"}</strong><small>v2 operations</small></div></div>
      </aside>

      <section className="content">
        <header><div><p className="eyebrow">REDPA AI · V2 · 10.3–10.5</p><h1>Operations Workspace</h1><p className="subtitle">Visualize workflows, approve sensitive actions and inspect semantic memory.</p></div><button onClick={() => void refresh()}>Refresh</button></header>
        {message && <div className="warning"><strong>Notice</strong><span>{message}</span></div>}

        <section id="overview" className="stats">
          <article><span>Platform</span><strong className={health?.status === "healthy" ? "good" : ""}>{health?.status || "—"}</strong><small>{healthyDeps}/{totalDeps} dependencies healthy</small></article>
          <article><span>Durable Workflows</span><strong>{workflows.length}</strong><small>Persisted executions</small></article>
          <article><span>Human Reviews</span><strong>{token ? pendingReviews : "Locked"}</strong><small>{token ? "Pending approvals" : "Sign in below"}</small></article>
          <article><span>Remote A2A</span><strong>{remotes ? `${connectedRemotes}/${remotes.total}` : "—"}</strong><small>{agents?.total ?? 0} registered agents</small></article>
        </section>

        <section className="panel" id="workflows">
          <div className="panelTitle"><div><p className="eyebrow">PHASE 10.3</p><h2>Durable Workflow Visualizer</h2></div><span className="pill">{workflows.length} workflows</span></div>
          <div className="workflowLayout">
            <div className="workflowList">
              {workflows.map(w => <button key={w.id} className={`workflowItem ${selected?.id === w.id ? "selectedWorkflow" : ""}`} onClick={() => setSelected(w)}><div className="workflowTop"><span className={`badge ${tone(w.status)}`}>{w.status}</span><small>{when(w.created_at)}</small></div><strong>{w.request}</strong><div className="meta"><span>{w.successful_subtasks} success</span><span>{w.failed_subtasks} failed</span>{w.approval_required && <span>approval</span>}</div></button>)}
              {!workflows.length && <div className="empty">No durable workflows yet.</div>}
            </div>
            <div className="canvas">{selected ? <WorkflowView workflow={selected} /> : <div className="emptyState"><b>WF</b><strong>Select a workflow</strong><p>See request → planner → specialist subtasks → approval → aggregate.</p></div>}</div>
          </div>
        </section>

        <section className="panel" id="reviews">
          <div className="panelTitle"><div><p className="eyebrow">PHASE 10.4</p><h2>Human Review Console</h2></div>{token && <button className="ghost" onClick={() => { localStorage.removeItem("redpa_access_token"); setToken(""); }}>Sign out</button>}</div>
          {!token ? <form className="login" onSubmit={login}><div><strong>Sign in to protected review actions</strong><p>Uses the existing JWT login endpoint.</p></div><input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required /><input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required /><button>Sign in</button></form> : <div className="reviewGrid">{(reviews?.items ?? []).map(review => <article className="reviewCard" key={review.id}><div className="workflowTop"><span className={`badge ${tone(review.status)}`}>{review.status}</span><small>{when(review.created_at)}</small></div><strong>{review.requested_action || "Human Review"}</strong><p>{review.reason}</p>{review.request_content && <div className="requestBox">{review.request_content}</div>}{review.status === "pending" && <><textarea placeholder="Optional reviewer feedback" value={feedback[review.id] || ""} onChange={e => setFeedback(v => ({ ...v, [review.id]: e.target.value }))} /><div className="actions"><button className="approve" onClick={() => void reviewAction(review, "approve")}>Approve</button><button className="reject" onClick={() => void reviewAction(review, "reject")}>Reject</button></div></>}{review.status === "approved" && <button className="resume" onClick={() => void reviewAction(review, "resume")}>Resume workflow</button>}</article>)}{reviews && !reviews.items.length && <div className="empty">No reviews found.</div>}</div>}
        </section>

        <section className="panel" id="memory">
          <div className="panelTitle"><div><p className="eyebrow">PHASE 10.5</p><h2>Agent Memory Explorer</h2></div><span className="pill">{memoryResults.length ? `${memoryResults.length} matches` : `${memories.length} memories`}</span></div>
          <form className="memorySearch" onSubmit={searchMemory}><input placeholder="Semantic memory search…" value={memoryQuery} onChange={e => setMemoryQuery(e.target.value)} /><input placeholder="Agent ID" value={memoryAgent} onChange={e => setMemoryAgent(e.target.value)} /><select value={memoryScope} onChange={e => setMemoryScope(e.target.value)}><option value="">All scopes</option><option>private</option><option>shared</option><option>workflow</option><option>user</option></select><select value={memoryKind} onChange={e => setMemoryKind(e.target.value)}><option value="">All kinds</option><option>fact</option><option>preference</option><option>summary</option><option>observation</option><option>decision</option><option>result</option></select><button>Search</button>{memoryResults.length > 0 && <button type="button" className="ghost" onClick={() => { setMemoryResults([]); setMemoryQuery(""); }}>Clear</button>}</form>
          <div className="memoryGrid">{memoryView.map(item => <article className="memoryCard" key={item.memory.id}><div className="memoryTop"><div><span className="tag red">{item.memory.kind}</span><span className="tag">{item.memory.scope}</span><span className="tag">{item.memory.agent_id}</span></div>{item.score >= 0 && <strong>{Math.round(item.score * 100)}</strong>}</div><p>{item.memory.content}</p><div className="importance"><span>Importance</span><div><i style={{ width: `${Math.min(100, Math.max(0, item.memory.importance * 100))}%` }} /></div><b>{item.memory.importance.toFixed(2)}</b></div><footer><span>{item.memory.embedding_status}</span><span>{when(item.memory.updated_at)}</span><button onClick={() => void deleteMemory(item.memory.id)}>Delete</button></footer></article>)}{!memoryView.length && <div className="empty">No memories found.</div>}</div>
        </section>

        <div className="twoCol" id="agents">
          <section className="panel"><div className="panelTitle"><div><p className="eyebrow">AGENTS</p><h2>Capability Discovery</h2></div><span className="pill">{agents?.total ?? 0} agents</span></div><form className="discover" onSubmit={discover}><input placeholder='Try "inspect database tables"' value={agentQuery} onChange={e => setAgentQuery(e.target.value)} /><button>Discover</button></form><div className="compact">{(agentMatches?.matches ?? []).map(m => <div key={`${m.agent_id}-${m.capability_name}`}><span><strong>{m.agent_name}</strong><small>{m.capability_name}</small></span><b>{Math.round(m.score * 100)}</b></div>)}{!agentMatches && (agents?.items ?? []).slice(0, 8).map(a => <div key={a.id}><span><strong>{a.name}</strong><small>{a.capability_names.slice(0, 3).join(" · ")}</small></span><span className={`badge ${tone(a.status)}`}>{a.status}</span></div>)}</div></section>
          <section className="panel"><div className="panelTitle"><div><p className="eyebrow">A2A</p><h2>Remote Specialists</h2></div><span className="pill">{remotes?.total ?? 0}</span></div><div className="compact">{(remotes?.items ?? []).map(a => <div key={a.name}><span><strong>{a.agent_name || a.name}</strong><small>{a.skills.slice(0, 3).join(" · ")}</small></span><span className={`badge ${a.connected ? "ok" : "bad"}`}>{a.connected ? "connected" : "offline"}</span></div>)}</div></section>
        </div>
      </section>
    </main>
  );
}

function WorkflowView({ workflow }: { workflow: Workflow }) {
  return <div className="visualizer"><div className="summary"><span className={`badge ${tone(workflow.status)}`}>{workflow.status}</span><strong>{workflow.request}</strong><small>{when(workflow.created_at)}</small></div><div className="flow"><Node title="Request" status="completed" /><Node title="Planner" status={workflow.status} /><div className="subtasks"><label>Specialist subtasks</label>{workflow.subtasks.length ? workflow.subtasks.map(s => <div className="subtask" key={s.id}><div><i className={`dotState ${tone(s.status)}`} /><strong>{s.subtask_key}</strong></div><p>{s.instruction}</p><small>{s.remote_agent || "local"} · {Math.round(s.execution_time_ms)} ms · attempt {s.attempt_count}</small>{s.error && <em>{s.error}</em>}</div>) : <div className="subtask"><strong>Planner-managed execution</strong><small>No persisted subtasks</small></div>}</div>{workflow.approval_required && <Node title="Human Review" status={workflow.approval_granted ? "approved" : "pending"} />}<Node title="Aggregate" status={workflow.status} /></div>{workflow.review_reason && <div className="notice"><b>Review reason</b><span>{workflow.review_reason}</span></div>}{workflow.aggregated_response && <details><summary>Aggregated response</summary><pre>{workflow.aggregated_response}</pre></details>}</div>;
}

function Node({ title, status }: { title: string; status: string }) {
  return <div className="nodeWrap"><div className="node"><i className={`dotState ${tone(status)}`} /><strong>{title}</strong><small>{status}</small></div><span>→</span></div>;
}
