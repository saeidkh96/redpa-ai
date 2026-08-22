"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type Dependency = { name: string; status: string; latency_ms?: number };
type Health = {
  status: string;
  service?: string;
  version?: string;
  environment?: string;
  dependencies?: Dependency[];
};

type Agent = {
  id: string;
  name: string;
  status: string;
  version?: string;
  capability_names: string[];
  supported_routes?: string[];
};
type AgentList = { items: Agent[]; total: number };

type RemoteAgent = {
  name: string;
  connected: boolean;
  agent_name?: string | null;
  agent_version?: string | null;
  base_url?: string;
  skills: string[];
};
type RemoteList = { items: RemoteAgent[]; total: number };

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
  max_parallelism?: number;
  timeout_seconds?: number;
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
  action_payload?: {
    resume_completed?: boolean;
    resumed_route?: string | null;
    resumed_assistant_message_id?: string | null;
    [key: string]: unknown;
  } | null;
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

type TokenResponse = { access_token: string; token_type?: string };

type McpServer = {
  name?: string;
  status?: string;
  enabled?: boolean;
  transport?: string;
  url?: string;
  base_url?: string;
  [key: string]: unknown;
};

type McpTool = {
  qualified_name?: string;
  name?: string;
  description?: string;
  server?: string;
  server_name?: string;
  [key: string]: unknown;
};

type Performance = {
  slow_request_threshold_ms?: number;
  slow_query_threshold_ms?: number;
  queued_jobs?: number;
  running_jobs?: number;
  dead_letter_jobs?: number;
  [key: string]: unknown;
};

type CapabilitySearch = {
  matches: {
    agent_id: string;
    agent_name: string;
    capability_name: string;
    score: number;
  }[];
};

const tone = (status?: string) => {
  const value = (status || "").toLowerCase();
  if (["healthy", "active", "completed", "approved", "connected", "ready"].includes(value)) return "ok";
  if (["running", "pending", "queued", "degraded", "paused"].includes(value)) return "warn";
  if (["failed", "rejected", "offline", "unhealthy", "unavailable"].includes(value)) return "bad";
  return "neutral";
};

const when = (value?: string) => value ? new Date(value).toLocaleString() : "-";

function normalizeArray(payload: unknown): any[] {
  if (Array.isArray(payload)) return payload;
  if (payload && typeof payload === "object") {
    const obj = payload as Record<string, unknown>;
    for (const key of ["items", "servers", "tools", "data", "results"]) {
      if (Array.isArray(obj[key])) return obj[key] as any[];
    }
  }
  return [];
}

export default function Dashboard() {
  const api = process.env.NEXT_PUBLIC_REDPA_API_URL || "http://localhost:8000";

  const [health, setHealth] = useState<Health | null>(null);
  const [live, setLive] = useState("unknown");
  const [ready, setReady] = useState("unknown");
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [metricsText, setMetricsText] = useState("");

  const [agents, setAgents] = useState<AgentList | null>(null);
  const [remotes, setRemotes] = useState<RemoteList | null>(null);
  const [agentQuery, setAgentQuery] = useState("");
  const [agentMatches, setAgentMatches] = useState<CapabilitySearch | null>(null);

  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);

  const [reviews, setReviews] = useState<ReviewList | null>(null);
  const [feedback, setFeedback] = useState<Record<string, string>>({});

  const [memories, setMemories] = useState<Memory[]>([]);
  const [memoryResults, setMemoryResults] = useState<MemorySearch[]>([]);
  const [memoryQuery, setMemoryQuery] = useState("");
  const [memoryAgent, setMemoryAgent] = useState("");
  const [memoryScope, setMemoryScope] = useState("");
  const [memoryKind, setMemoryKind] = useState("");

  const [mcpServers, setMcpServers] = useState<McpServer[]>([]);
  const [mcpTools, setMcpTools] = useState<McpTool[]>([]);
  const [mcpHealth, setMcpHealth] = useState<unknown>(null);
  const [selectedTool, setSelectedTool] = useState("");
  const [toolArgs, setToolArgs] = useState("{}");
  const [toolResult, setToolResult] = useState<unknown>(null);

  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("redpa_access_token");
    if (saved) setToken(saved);
  }, []);

  const request = useCallback(async <T,>(
    path: string,
    init?: RequestInit,
    auth = false,
  ): Promise<T> => {
    const headers = new Headers(init?.headers || {});
    if (auth && token) headers.set("Authorization", `Bearer ${token}`);

    const response = await fetch(`${api}${path}`, {
      ...init,
      headers,
      cache: "no-store",
    });

    if (!response.ok) {
      let detail = `${response.status} ${response.statusText}`;
      try {
        const body = await response.json();
        detail = body.detail || body?.error?.message || detail;
      } catch {}
      throw new Error(detail);
    }

    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }, [api, token]);

  const refreshPublic = useCallback(async () => {
    const results = await Promise.allSettled([
      request<Health>("/api/v1/platform/health"),
      request<Record<string, unknown>>("/api/v1/platform/live"),
      request<Record<string, unknown>>("/api/v1/platform/ready"),
      request<Performance>("/api/v1/performance/snapshot"),
      request<AgentList>("/api/v1/agents"),
      request<RemoteList>("/api/v1/agents/remotes"),
      request<Workflow[]>("/api/v1/agents/distributed/durable?limit=50"),
      request<Memory[]>("/api/v1/memory?limit=100"),
      fetch(`${api}/api/v1/metrics`, { cache: "no-store" }).then(async r => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
        return r.text();
      }),
    ]);

    if (results[0].status === "fulfilled") setHealth(results[0].value);
    if (results[1].status === "fulfilled") setLive(String(results[1].value.status ?? "live"));
    if (results[2].status === "fulfilled") setReady(String(results[2].value.status ?? "ready"));
    if (results[3].status === "fulfilled") setPerformance(results[3].value);
    if (results[4].status === "fulfilled") setAgents(results[4].value);
    if (results[5].status === "fulfilled") setRemotes(results[5].value);
    if (results[6].status === "fulfilled") setWorkflows(results[6].value);
    if (results[7].status === "fulfilled") setMemories(results[7].value);
    if (results[8].status === "fulfilled") setMetricsText(results[8].value);

    const errors = results
      .filter(r => r.status === "rejected")
      .map(r => r.status === "rejected" ? r.reason?.message : "")
      .filter(Boolean);

    setMessage(errors.length ? errors.join(" | ") : null);
    setLastUpdated(new Date().toLocaleTimeString());
  }, [api, request]);

  const refreshProtected = useCallback(async () => {
    if (!token) {
      setReviews(null);
      setMcpServers([]);
      setMcpTools([]);
      setMcpHealth(null);
      return;
    }

    const results = await Promise.allSettled([
      request<ReviewList>("/api/v1/reviews?limit=100&offset=0", undefined, true),
      request<unknown>("/api/v1/mcp/servers", undefined, true),
      request<unknown>("/api/v1/mcp/health", undefined, true),
      request<unknown>("/api/v1/mcp/tools", undefined, true),
    ]);

    if (results[0].status === "fulfilled") setReviews(results[0].value);
    if (results[1].status === "fulfilled") setMcpServers(normalizeArray(results[1].value) as McpServer[]);
    if (results[2].status === "fulfilled") setMcpHealth(results[2].value);
    if (results[3].status === "fulfilled") setMcpTools(normalizeArray(results[3].value) as McpTool[]);
  }, [request, token]);

  useEffect(() => {
    void refreshPublic();
    void refreshProtected();
    const id = setInterval(() => {
      void refreshPublic();
      void refreshProtected();
    }, 15000);
    return () => clearInterval(id);
  }, [refreshPublic, refreshProtected]);

  const healthyDeps = health?.dependencies?.filter(d => d.status === "healthy").length ?? 0;
  const totalDeps = health?.dependencies?.length ?? 0;
  const pendingReviews = reviews?.items.filter(r => r.status === "pending").length ?? 0;
  const connectedRemotes = remotes?.items.filter(r => r.connected).length ?? 0;

  const metricValue = (name: string) => {
    const row = metricsText.split(/\r?\n/).find(line => line.startsWith(`${name} `));
    if (!row) return "-";
    const value = Number(row.slice(name.length).trim());
    return Number.isFinite(value) ? value.toFixed(0) : "-";
  };

  const login = async (event: FormEvent) => {
    event.preventDefault();
    setBusy("login");
    setMessage(null);
    try {
      const form = new URLSearchParams();
      form.set("username", email);
      form.set("password", password);
      const result = await request<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });
      localStorage.setItem("redpa_access_token", result.access_token);
      setToken(result.access_token);
      setPassword("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Login failed");
    } finally {
      setBusy("");
    }
  };

  const logout = () => {
    localStorage.removeItem("redpa_access_token");
    setToken("");
    setReviews(null);
    setMcpServers([]);
    setMcpTools([]);
  };

  const reviewAction = async (review: Review, action: "approve" | "reject" | "resume") => {
    setBusy(review.id);
    setMessage(null);
    try {
      const init: RequestInit = action === "resume"
        ? { method: "POST" }
        : {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ feedback: feedback[review.id] || null }),
          };

      await request(`/api/v1/reviews/${review.id}/${action}`, init, true);
      await refreshProtected();
      await refreshPublic();
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Review action failed";
      if (action === "resume" && /already.*resum|resum.*already/i.test(detail)) {
        setMessage("Workflow was already resumed.");
        await refreshProtected();
      } else {
        setMessage(detail);
      }
    } finally {
      setBusy("");
    }
  };

  const searchMemory = async (event: FormEvent) => {
    event.preventDefault();
    if (!memoryQuery.trim()) {
      setMemoryResults([]);
      return;
    }
    setBusy("memory");
    try {
      const payload: Record<string, unknown> = {
        query: memoryQuery.trim(),
        limit: 20,
        min_score: 0.2,
        include_shared: true,
      };
      if (memoryAgent.trim()) payload.agent_id = memoryAgent.trim();
      if (memoryScope) payload.scopes = [memoryScope];
      if (memoryKind) payload.kinds = [memoryKind];

      setMemoryResults(await request<MemorySearch[]>("/api/v1/memory/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Memory search failed");
    } finally {
      setBusy("");
    }
  };

  const deleteMemory = async (id: string) => {
    if (!confirm("Delete this memory?")) return;
    setBusy(id);
    try {
      await request(`/api/v1/memory/${id}`, { method: "DELETE" });
      setMemoryResults(current => current.filter(x => x.memory.id !== id));
      await refreshPublic();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Delete failed");
    } finally {
      setBusy("");
    }
  };

  const discoverAgent = async (event: FormEvent) => {
    event.preventDefault();
    if (!agentQuery.trim()) return;
    try {
      setAgentMatches(await request<CapabilitySearch>(
        `/api/v1/agents/discover?query=${encodeURIComponent(agentQuery.trim())}&limit=8`
      ));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Agent discovery failed");
    }
  };

  const reloadMcp = async () => {
    setBusy("mcp-reload");
    try {
      await request("/api/v1/mcp/servers/reload", { method: "POST" }, true);
      await refreshProtected();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "MCP reload failed");
    } finally {
      setBusy("");
    }
  };

  const executeTool = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedTool) return;
    setBusy("tool");
    setToolResult(null);
    try {
      let args: Record<string, unknown>;
      try {
        args = toolArgs.trim() ? JSON.parse(toolArgs) : {};
      } catch {
        throw new Error("Arguments must be valid JSON.");
      }

      const result = await request<unknown>("/api/v1/mcp/tools/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ qualified_name: selectedTool, arguments: args }),
      }, true);
      setToolResult(result);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Tool execution failed");
    } finally {
      setBusy("");
    }
  };

  const visibleMemories = memoryResults.length
    ? memoryResults.map(x => ({ memory: x.memory, score: x.score }))
    : memories.map(memory => ({ memory, score: null as number | null }));

  const securityChecks = useMemo(() => [
    ["JWT control plane", token ? "ok" : "neutral", token ? "Authenticated session active" : "Sign in to validate protected APIs"],
    ["Liveness", tone(live), `/api/v1/platform/live: ${live}`],
    ["Readiness", tone(ready), `/api/v1/platform/ready: ${ready}`],
    ["Deep health", tone(health?.status), `${healthyDeps}/${totalDeps} dependencies healthy`],
    ["MCP boundary", token ? "ok" : "neutral", token ? `${mcpServers.length} protected servers visible` : "Protected until JWT authentication"],
    ["Metrics", metricsText ? "ok" : "warn", metricsText ? "Prometheus exposition available" : "Metrics unavailable"],
  ], [token, live, ready, health?.status, healthyDeps, totalDeps, mcpServers.length, metricsText]);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/logo.png" alt="RedPA AI" />
          <div><strong>RedPA AI</strong><span>Control Center</span></div>
        </div>
        <nav>
          <a href="#overview">Overview</a>
          <a href="#agents">Agents</a>
          <a href="#workflows">Workflows</a>
          <a href="#reviews">Human Reviews</a>
          <a href="#memory">Memory</a>
          <a href="#mcp">MCP & Tools</a>
          <a href="#operations">Operations</a>
          <a className="selected" href="#security">Security</a>
          <a href="#release">Release</a>
        </nav>
        <div className="sidebarFooter">
          <span className={`dot ${health?.status === "healthy" ? "dotHealthy" : ""}`} />
          <div><strong>{health?.status || "Connecting"}</strong><small>{lastUpdated || "loading..."}</small></div>
        </div>
      </aside>

      <section className="content">
        <header>
          <div>
            <p className="eyebrow">REDPA AI | V20 | PRODUCTION</p>
            <h1>Operations Control Center</h1>
            <p className="subtitle">Agents, workflows, human approval, memory, MCP tools, observability, security and release readiness.</p>
          </div>
          <button onClick={() => { void refreshPublic(); void refreshProtected(); }}>Refresh all</button>
        </header>

        {message && <div className="notice"><strong>Notice</strong><span>{message}</span></div>}

        <section id="overview" className="stats">
          <article><span>Platform</span><strong className={health?.status === "healthy" ? "good" : ""}>{health?.status ?? "-"}</strong><small>v{health?.version ?? "-"}</small></article>
          <article><span>Dependencies</span><strong>{healthyDeps}/{totalDeps}</strong><small>healthy</small></article>
          <article><span>Agents</span><strong>{agents?.total ?? 0}</strong><small>{connectedRemotes}/{remotes?.total ?? 0} remote connected</small></article>
          <article><span>Release</span><strong>V20.0.0</strong><small>production</small></article>
        </section>

        <section className="panel" id="agents">
          <PanelTitle eyebrow="PHASE 10.2" title="Agent Control Center" badge={`${agents?.total ?? 0} agents`} />
          <form className="inlineForm" onSubmit={discoverAgent}>
            <input value={agentQuery} onChange={e => setAgentQuery(e.target.value)} placeholder='Try "inspect Docker containers"' />
            <button>Discover</button>
          </form>
          <div className="cardGrid">
            {(agentMatches?.matches ?? []).map(match => (
              <article className="miniCard" key={`${match.agent_id}-${match.capability_name}`}>
                <span className="score">{Math.round(match.score * 100)}</span>
                <strong>{match.agent_name}</strong><small>{match.capability_name}</small>
              </article>
            ))}
            {!agentMatches && (agents?.items ?? []).map(agent => (
              <article className="miniCard" key={agent.id}>
                <span className={`status ${tone(agent.status)}`}>{agent.status}</span>
                <strong>{agent.name}</strong>
                <small>{agent.capability_names.slice(0, 4).join(" | ")}</small>
              </article>
            ))}
          </div>
        </section>

        <section className="panel" id="workflows">
          <PanelTitle eyebrow="PHASE 10.3" title="Durable Workflow Visualizer" badge={`${workflows.length} workflows`} />
          <div className="workflowLayout">
            <div className="workflowList">
              {workflows.map(workflow => (
                <button key={workflow.id} className={selectedWorkflow?.id === workflow.id ? "selected" : ""} onClick={() => setSelectedWorkflow(workflow)}>
                  <span className={`status ${tone(workflow.status)}`}>{workflow.status}</span>
                  <strong>{workflow.request}</strong>
                  <small>{when(workflow.created_at)}</small>
                </button>
              ))}
            </div>
            <div className="workflowCanvas">
              {selectedWorkflow ? <WorkflowView workflow={selectedWorkflow} /> : <div className="empty">Select a workflow to inspect its execution graph.</div>}
            </div>
          </div>
        </section>

        <section className="panel" id="reviews">
          <div className="panelTitle">
            <div><p className="eyebrow">PHASE 10.4</p><h2>Human Review Console</h2></div>
            {token && <button className="secondary" onClick={logout}>Sign out</button>}
          </div>
          {!token ? (
            <form className="loginForm" onSubmit={login}>
              <input type="email" required placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
              <input type="password" required placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
              <button disabled={busy === "login"}>{busy === "login" ? "Signing in..." : "Sign in"}</button>
            </form>
          ) : (
            <div className="cardGrid">
              {(reviews?.items ?? []).map(review => (
                <article className="reviewCard" key={review.id}>
                  <div className="row"><span className={`status ${tone(review.status)}`}>{review.status}</span><small>{when(review.created_at)}</small></div>
                  <strong>{review.requested_action || "Human review"}</strong>
                  <p>{review.reason}</p>
                  {review.request_content && <div className="codeBox">{review.request_content}</div>}
                  {review.status === "pending" && <>
                    <textarea value={feedback[review.id] || ""} onChange={e => setFeedback(x => ({ ...x, [review.id]: e.target.value }))} placeholder="Optional feedback" />
                    <div className="row actions">
                      <button className="approve" onClick={() => void reviewAction(review, "approve")}>Approve</button>
                      <button className="reject" onClick={() => void reviewAction(review, "reject")}>Reject</button>
                    </div>
                  </>}
                  {review.status === "approved" && (
                    review.action_payload?.resume_completed || review.action_payload?.resumed_assistant_message_id
                      ? <div className="resumeDone"><strong>Workflow resumed</strong><span>Route: {String(review.action_payload?.resumed_route || "completed")}</span></div>
                      : <button className="resume" onClick={() => void reviewAction(review, "resume")}>Resume workflow</button>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="panel" id="memory">
          <PanelTitle eyebrow="PHASE 10.5" title="Agent Memory Explorer" badge={memoryResults.length ? `${memoryResults.length} matches` : `${memories.length} memories`} />
          <form className="memoryForm" onSubmit={searchMemory}>
            <input value={memoryQuery} onChange={e => setMemoryQuery(e.target.value)} placeholder="Semantic memory search..." />
            <input value={memoryAgent} onChange={e => setMemoryAgent(e.target.value)} placeholder="Agent ID" />
            <select value={memoryScope} onChange={e => setMemoryScope(e.target.value)}><option value="">All scopes</option><option>private</option><option>shared</option><option>workflow</option><option>user</option></select>
            <select value={memoryKind} onChange={e => setMemoryKind(e.target.value)}><option value="">All kinds</option><option>fact</option><option>preference</option><option>summary</option><option>observation</option><option>decision</option><option>result</option></select>
            <button>Search</button>
            <button type="button" className="secondary" onClick={() => { setMemoryResults([]); setMemoryQuery(""); }}>Clear</button>
          </form>
          <div className="memoryGrid">
            {visibleMemories.map(({ memory, score }) => (
              <article className="memoryCard" key={memory.id}>
                <div className="row"><div className="tags"><span>{memory.kind}</span><span>{memory.scope}</span><span>{memory.agent_id}</span></div>{score !== null && <strong className="score">{Math.round(score * 100)}</strong>}</div>
                <p>{memory.content}</p>
                <small>Importance {memory.importance.toFixed(2)} | {memory.embedding_status} | {when(memory.updated_at)}</small>
                <button className="delete" disabled={busy === memory.id} onClick={() => void deleteMemory(memory.id)}>Delete</button>
              </article>
            ))}
          </div>
        </section>

        <section className="panel" id="mcp">
          <div className="panelTitle">
            <div><p className="eyebrow">PHASE 10.6</p><h2>MCP & Tool Console</h2></div>
            <div className="row"><span className="pill">{mcpTools.length} tools</span>{token && <button className="secondary" onClick={() => void reloadMcp()}>Reload registry</button>}</div>
          </div>
          {!token ? <div className="authNotice">Sign in from Human Reviews to unlock the protected MCP control plane.</div> : (
            <div className="mcpLayout">
              <div>
                <h3>Servers</h3>
                <div className="stack">
                  {mcpServers.map((server, i) => {
                    const name = String(server.name || `server-${i + 1}`);
                    const status = String(server.status || (server.enabled === false ? "disabled" : "active"));
                    return <div className="serverRow" key={name}><strong>{name}</strong><span className={`status ${tone(status)}`}>{status}</span></div>;
                  })}
                </div>
                <details><summary>Health payload</summary><pre>{JSON.stringify(mcpHealth, null, 2)}</pre></details>
              </div>
              <div>
                <h3>Tool catalog</h3>
                <div className="toolList">
                  {mcpTools.map((tool, i) => {
                    const qn = String(tool.qualified_name || tool.name || `tool-${i + 1}`);
                    return <button key={qn} className={selectedTool === qn ? "selected" : ""} onClick={() => setSelectedTool(qn)}><strong>{qn}</strong><small>{String(tool.description || "MCP tool")}</small></button>;
                  })}
                </div>
              </div>
              <form className="toolRunner" onSubmit={executeTool}>
                <h3>Tool runner</h3>
                <select value={selectedTool} onChange={e => setSelectedTool(e.target.value)}>
                  <option value="">Select a tool</option>
                  {mcpTools.map((tool, i) => {
                    const qn = String(tool.qualified_name || tool.name || `tool-${i + 1}`);
                    return <option key={qn} value={qn}>{qn}</option>;
                  })}
                </select>
                <textarea value={toolArgs} onChange={e => setToolArgs(e.target.value)} spellCheck={false} />
                <button disabled={!selectedTool || busy === "tool"}>{busy === "tool" ? "Executing..." : "Execute tool"}</button>
                {toolResult !== null && <pre className="result">{JSON.stringify(toolResult, null, 2)}</pre>}
              </form>
            </div>
          )}
        </section>

        <section className="panel" id="operations">
          <PanelTitle eyebrow="PHASE 10.7" title="Observability & Operations" badge="live" />
          <div className="opsGrid">
            <div className="metricCards">
              <Metric label="Queued jobs" value={performance?.queued_jobs ?? 0} />
              <Metric label="Running jobs" value={performance?.running_jobs ?? 0} />
              <Metric label="Dead letter" value={performance?.dead_letter_jobs ?? 0} />
              <Metric label="Slow requests" value={metricValue("redpa_slow_requests_total")} />
            </div>
            <div className="stack">
              {(health?.dependencies ?? []).map(dep => <div className="depRow" key={dep.name}><span className={`dot ${dep.status === "healthy" ? "dotHealthy" : ""}`} /><strong>{dep.name}</strong><small>{dep.latency_ms?.toFixed(1) ?? "-"} ms</small><span className={`status ${tone(dep.status)}`}>{dep.status}</span></div>)}
            </div>
            <div className="links">
              <a href="http://localhost:9090" target="_blank" rel="noreferrer">Prometheus <span>:9090</span></a>
              <a href="http://localhost:3000" target="_blank" rel="noreferrer">Grafana <span>:3000</span></a>
              <a href="http://localhost:3200/ready" target="_blank" rel="noreferrer">Tempo <span>:3200</span></a>
              <a href={`${api}/api/v1/metrics`} target="_blank" rel="noreferrer">Raw metrics <span>API</span></a>
            </div>
          </div>
        </section>

        <section className="panel" id="security">
          <PanelTitle eyebrow="PHASE 10.8" title="Security & Production Readiness" badge="release gate" />
          <div className="securityGrid">
            <div className="stack">
              {securityChecks.map(([name, state, detail]) => (
                <article className="securityRow" key={name}>
                  <span className={`check ${state}`}>{state === "ok" ? "OK" : state === "warn" ? "!" : "i"}</span>
                  <div><strong>{name}</strong><small>{detail}</small></div>
                </article>
              ))}
            </div>
            <div className="prodChecklist">
              <h3>Production controls</h3>
              {[
                "Strong SECRET_KEY and JWT_SECRET_KEY",
                "DEBUG=false",
                "EXPOSE_ERROR_DETAILS=false",
                "REQUIRE_HTTPS=true behind TLS ingress",
                "Restricted ALLOWED_HOSTS and CORS",
                "Persistent stateful volumes",
                "Health probes enabled",
                "Telemetry retention reviewed",
                "No real credentials committed",
              ].map(item => <div className="prodChecklistRow" key={item}><span className="prodChecklistOk">OK</span><p>{item}</p></div>)}
              <small>Checklist items are release requirements, not claims about the current development environment.</small>
            </div>
          </div>
        </section>

        <section className="panel" id="release">
          <PanelTitle eyebrow="V3" title="Release Readiness" badge="v3.0.0" />
          <div className="releaseGrid">
            <Metric label="Platform" value={health?.status === "healthy" ? "Ready" : "Check"} />
            <Metric label="Frontend" value="Online" />
            <Metric label="MCP tools" value={token ? mcpTools.length : "Auth"} />
            <Metric label="Reviews pending" value={token ? pendingReviews : "Auth"} />
          </div>
          <div className="releaseBox">
            <strong>Final validation</strong>
            <p>
              Run <code>.\VERIFY_V3_PHASES_17_18_19_RUNTIME.ps1</code>. After the runtime,
              regression, security, and release checks pass, build the release artifact with{" "}
              <code>.\BUILD_V3_RELEASE.ps1</code>.
            </p>
          </div>
        </section>
      </section>
    </main>
  );
}

function PanelTitle({ eyebrow, title, badge }: { eyebrow: string; title: string; badge: string }) {
  return <div className="panelTitle"><div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div><span className="pill">{badge}</span></div>;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <article className="metric"><span>{label}</span><strong>{String(value)}</strong></article>;
}

function WorkflowView({ workflow }: { workflow: Workflow }) {
  return <div className="flow">
    <div className="flowSummary"><span className={`status ${tone(workflow.status)}`}>{workflow.status}</span><strong>{workflow.request}</strong></div>
    <div className="flowLine">
      <FlowNode title="Request" detail="Created" state="completed" />
      <span>-&gt;</span>
      <FlowNode title="Planner" detail={`${workflow.subtasks.length} subtasks`} state={workflow.status} />
      <span>-&gt;</span>
      <div className="subtasks">
        <small>Specialist subtasks</small>
        {workflow.subtasks.map(task => <div key={task.id}><span className={`status ${tone(task.status)}`}>{task.status}</span><strong>{task.subtask_key}</strong><p>{task.instruction}</p><small>{task.remote_agent || "local"} | {task.execution_time_ms.toFixed(0)} ms | attempt {task.attempt_count}</small></div>)}
      </div>
      {workflow.approval_required && <><span>-&gt;</span><FlowNode title="Human Review" detail={workflow.approval_granted ? "Approved" : "Required"} state={workflow.approval_granted ? "approved" : "pending"} /></>}
      <span>-&gt;</span>
      <FlowNode title="Aggregate" detail={`${workflow.successful_subtasks} success | ${workflow.failed_subtasks} failed`} state={workflow.status} />
    </div>
    {workflow.aggregated_response && <details><summary>Aggregated response</summary><pre>{workflow.aggregated_response}</pre></details>}
  </div>;
}

function FlowNode({ title, detail, state }: { title: string; detail: string; state: string }) {
  return <div className="flowNode"><span className={`status ${tone(state)}`}>{state}</span><strong>{title}</strong><small>{detail}</small></div>;
}
