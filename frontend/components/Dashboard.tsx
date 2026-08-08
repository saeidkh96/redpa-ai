"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type Dependency = {
  name: string;
  status: string;
  latency_ms?: number;
};

type Health = {
  status: string;
  service?: string;
  version?: string;
  environment?: string;
  dependencies?: Dependency[];
};

type AgentSummary = {
  id: string;
  name: string;
  version: string;
  status: string;
  capability_names: string[];
  supported_routes: string[];
};

type AgentList = {
  items: AgentSummary[];
  total: number;
};

type AgentHealth = {
  status: string;
  total_agents: number;
  active_agents: number;
  degraded_agents: number;
  offline_agents: number;
  checked_at: string;
};

type Capability = {
  name: string;
  description: string;
  tags: string[];
  input_modes: string[];
  output_modes: string[];
  examples: string[];
};

type AgentCard = {
  id: string;
  name: string;
  version: string;
  description: string;
  status: string;
  capabilities: Capability[];
  supported_routes: string[];
  endpoint?: {
    url: string;
    transport: string;
  } | null;
};

type RemoteAgent = {
  name: string;
  base_url: string;
  enabled: boolean;
  connected: boolean;
  agent_name?: string | null;
  agent_version?: string | null;
  protocol_bindings: string[];
  skills: string[];
  last_checked_at?: string | null;
  error?: string | null;
};

type RemoteAgentList = {
  items: RemoteAgent[];
  total: number;
};

type CapabilityMatch = {
  agent_id: string;
  agent_name: string;
  capability_name: string;
  capability_description: string;
  matched_tags: string[];
  score: number;
};

type DiscoveryResponse = {
  query: string;
  matches: CapabilityMatch[];
  total: number;
};

type ApiState<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
};

const initialApiState = <T,>(): ApiState<T> => ({
  data: null,
  error: null,
  loading: true,
});

function statusClass(status?: string): string {
  if (status === "healthy" || status === "active" || status === "connected") {
    return "positive";
  }
  if (status === "degraded") {
    return "warningState";
  }
  if (status === "offline" || status === "unhealthy") {
    return "negative";
  }
  return "neutral";
}

export default function Dashboard() {
  const apiBase =
    process.env.NEXT_PUBLIC_REDPA_API_URL || "http://localhost:8000";

  const [platform, setPlatform] = useState<ApiState<Health>>(initialApiState());
  const [agents, setAgents] = useState<ApiState<AgentList>>(initialApiState());
  const [agentHealth, setAgentHealth] =
    useState<ApiState<AgentHealth>>(initialApiState());
  const [remoteAgents, setRemoteAgents] =
    useState<ApiState<RemoteAgentList>>(initialApiState());

  const [selectedAgent, setSelectedAgent] = useState<AgentCard | null>(null);
  const [selectedLoading, setSelectedLoading] = useState(false);
  const [selectedError, setSelectedError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [discovery, setDiscovery] = useState<DiscoveryResponse | null>(null);
  const [discoveryLoading, setDiscoveryLoading] = useState(false);
  const [discoveryError, setDiscoveryError] = useState<string | null>(null);

  const [lastUpdated, setLastUpdated] = useState("");

  const fetchJson = useCallback(
    async <T,>(path: string): Promise<T> => {
      const response = await fetch(`${apiBase}${path}`, {
        cache: "no-store",
      });

      if (!response.ok) {
        let message = `${response.status} ${response.statusText}`;
        try {
          const body = await response.json();
          message = body.detail || message;
        } catch {
          // Keep the HTTP status when the response is not JSON.
        }
        throw new Error(message);
      }

      return (await response.json()) as T;
    },
    [apiBase]
  );

  const refresh = useCallback(async () => {
    const [platformResult, agentsResult, healthResult, remoteResult] =
      await Promise.allSettled([
        fetchJson<Health>("/api/v1/platform/health"),
        fetchJson<AgentList>("/api/v1/agents"),
        fetchJson<AgentHealth>("/api/v1/agents/health"),
        fetchJson<RemoteAgentList>("/api/v1/agents/remotes"),
      ]);

    setPlatform(
      platformResult.status === "fulfilled"
        ? { data: platformResult.value, error: null, loading: false }
        : {
            data: null,
            error: platformResult.reason?.message ?? "Platform health unavailable",
            loading: false,
          }
    );

    setAgents(
      agentsResult.status === "fulfilled"
        ? { data: agentsResult.value, error: null, loading: false }
        : {
            data: null,
            error: agentsResult.reason?.message ?? "Agent registry unavailable",
            loading: false,
          }
    );

    setAgentHealth(
      healthResult.status === "fulfilled"
        ? { data: healthResult.value, error: null, loading: false }
        : {
            data: null,
            error: healthResult.reason?.message ?? "Agent health unavailable",
            loading: false,
          }
    );

    setRemoteAgents(
      remoteResult.status === "fulfilled"
        ? { data: remoteResult.value, error: null, loading: false }
        : {
            data: null,
            error: remoteResult.reason?.message ?? "Remote agents unavailable",
            loading: false,
          }
    );

    setLastUpdated(new Date().toLocaleTimeString());
  }, [fetchJson]);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 15000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const openAgent = async (agentId: string) => {
    setSelectedLoading(true);
    setSelectedError(null);

    try {
      const card = await fetchJson<AgentCard>(
        `/api/v1/agents/${encodeURIComponent(agentId)}`
      );
      setSelectedAgent(card);
    } catch (error) {
      setSelectedError(
        error instanceof Error ? error.message : "Could not load Agent Card"
      );
    } finally {
      setSelectedLoading(false);
    }
  };

  const discover = async (event: FormEvent) => {
    event.preventDefault();

    const trimmed = query.trim();
    if (!trimmed) {
      setDiscovery(null);
      setDiscoveryError(null);
      return;
    }

    setDiscoveryLoading(true);
    setDiscoveryError(null);

    try {
      const result = await fetchJson<DiscoveryResponse>(
        `/api/v1/agents/discover?query=${encodeURIComponent(trimmed)}&limit=10`
      );
      setDiscovery(result);
    } catch (error) {
      setDiscovery(null);
      setDiscoveryError(
        error instanceof Error ? error.message : "Capability discovery failed"
      );
    } finally {
      setDiscoveryLoading(false);
    }
  };

  const dependencyCounts = useMemo(() => {
    const dependencies = platform.data?.dependencies ?? [];
    return {
      healthy: dependencies.filter((item) => item.status === "healthy").length,
      total: dependencies.length,
    };
  }, [platform.data]);

  const connectedRemoteCount =
    remoteAgents.data?.items.filter((agent) => agent.connected).length ?? 0;

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/logo.png" alt="RedPA AI" />
          <div>
            <strong>RedPA AI</strong>
            <span>Control Center</span>
          </div>
        </div>

        <nav>
          <a href="#overview">Overview</a>
          <a className="selected" href="#agents">
            Agents
          </a>
          <a href="#discovery">Discovery</a>
          <a href="#remote-agents">Remote Agents</a>
          <a href="#runtime">Runtime</a>
        </nav>

        <div className="sidebarFooter">
          <span
            className={`dot ${
              platform.data?.status === "healthy" ? "dotHealthy" : ""
            }`}
          />
          <div>
            <strong>
              {platform.data?.status === "healthy"
                ? "Platform healthy"
                : "Platform connection"}
            </strong>
            <small>{lastUpdated ? `Updated ${lastUpdated}` : "Connecting…"}</small>
          </div>
        </div>
      </aside>

      <section className="content">
        <header>
          <div>
            <p className="eyebrow">REDPA AI · V2 · PHASE 10.2</p>
            <h1>Agent Control Center</h1>
            <p className="subtitle">
              Live visibility into the built-in agent registry, A2A specialists,
              capabilities and runtime status.
            </p>
          </div>
          <button onClick={() => void refresh()}>Refresh all</button>
        </header>

        <section id="overview" className="stats">
          <article>
            <span>Registry</span>
            <strong>{agentHealth.data?.total_agents ?? agents.data?.total ?? "—"}</strong>
            <small>Total registered agents</small>
          </article>
          <article>
            <span>Active</span>
            <strong className="good">{agentHealth.data?.active_agents ?? "—"}</strong>
            <small>Healthy built-in agents</small>
          </article>
          <article>
            <span>Remote A2A</span>
            <strong>
              {remoteAgents.data
                ? `${connectedRemoteCount}/${remoteAgents.data.total}`
                : "—"}
            </strong>
            <small>Connected remote agents</small>
          </article>
          <article>
            <span>Dependencies</span>
            <strong>
              {dependencyCounts.total
                ? `${dependencyCounts.healthy}/${dependencyCounts.total}`
                : "—"}
            </strong>
            <small>Healthy platform services</small>
          </article>
        </section>

        {(agents.error || agentHealth.error || remoteAgents.error) && (
          <div className="warning">
            <strong>Some control-plane data could not be loaded.</strong>
            <span>
              {[agents.error, agentHealth.error, remoteAgents.error]
                .filter(Boolean)
                .join(" · ")}
            </span>
          </div>
        )}

        <section className="panel" id="agents">
          <div className="panelTitle">
            <div>
              <p className="eyebrow">BUILT-IN REGISTRY</p>
              <h2>Registered agents</h2>
            </div>
            <span className="pill">
              {agents.loading ? "Loading" : `${agents.data?.total ?? 0} agents`}
            </span>
          </div>

          <div className="agentCards">
            {(agents.data?.items ?? []).map((agent) => (
              <button
                type="button"
                className="agentCard"
                key={agent.id}
                onClick={() => void openAgent(agent.id)}
              >
                <div className="agentCardTop">
                  <div className="agentMonogram">
                    {agent.name.slice(0, 2).toUpperCase()}
                  </div>
                  <span className={`stateBadge ${statusClass(agent.status)}`}>
                    {agent.status}
                  </span>
                </div>

                <strong>{agent.name}</strong>
                <small className="agentId">{agent.id}</small>

                <div className="tagRow">
                  {agent.capability_names.slice(0, 4).map((capability) => (
                    <span className="tag" key={capability}>
                      {capability}
                    </span>
                  ))}
                  {agent.capability_names.length > 4 && (
                    <span className="tag">
                      +{agent.capability_names.length - 4}
                    </span>
                  )}
                </div>

                <div className="agentFooter">
                  <span>v{agent.version}</span>
                  <span>{agent.supported_routes.length} routes</span>
                </div>
              </button>
            ))}

            {!agents.loading && !agents.data?.items.length && (
              <div className="empty largeEmpty">No agents are registered.</div>
            )}
          </div>
        </section>

        <div className="twoColumn">
          <section className="panel" id="discovery">
            <div className="panelTitle">
              <div>
                <p className="eyebrow">CAPABILITY ROUTING</p>
                <h2>Discover an agent</h2>
              </div>
            </div>

            <form className="discoveryForm" onSubmit={discover}>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder='Try "inspect Docker containers"'
                maxLength={500}
              />
              <button type="submit" disabled={discoveryLoading}>
                {discoveryLoading ? "Searching…" : "Discover"}
              </button>
            </form>

            {discoveryError && <div className="inlineError">{discoveryError}</div>}

            <div className="matchList">
              {(discovery?.matches ?? []).map((match) => (
                <button
                  className="match"
                  type="button"
                  key={`${match.agent_id}-${match.capability_name}`}
                  onClick={() => void openAgent(match.agent_id)}
                >
                  <div>
                    <strong>{match.agent_name}</strong>
                    <span>{match.capability_name}</span>
                    <p>{match.capability_description}</p>
                  </div>
                  <div className="score">
                    {(match.score * 100).toFixed(0)}
                    <small>score</small>
                  </div>
                </button>
              ))}

              {discovery && discovery.matches.length === 0 && (
                <div className="empty">No matching capability was found.</div>
              )}

              {!discovery && (
                <div className="empty">
                  Search the live agent registry by task or capability.
                </div>
              )}
            </div>
          </section>

          <section className="panel" id="runtime">
            <div className="panelTitle">
              <div>
                <p className="eyebrow">REGISTRY HEALTH</p>
                <h2>Agent runtime</h2>
              </div>
              <span className={`stateBadge ${statusClass(agentHealth.data?.status)}`}>
                {agentHealth.data?.status ?? "unknown"}
              </span>
            </div>

            <div className="runtimeBars">
              <RuntimeMetric
                label="Active"
                value={agentHealth.data?.active_agents ?? 0}
                total={agentHealth.data?.total_agents ?? 0}
                kind="active"
              />
              <RuntimeMetric
                label="Degraded"
                value={agentHealth.data?.degraded_agents ?? 0}
                total={agentHealth.data?.total_agents ?? 0}
                kind="degraded"
              />
              <RuntimeMetric
                label="Offline"
                value={agentHealth.data?.offline_agents ?? 0}
                total={agentHealth.data?.total_agents ?? 0}
                kind="offline"
              />
            </div>

            <div className="platformInfo">
              <InfoRow label="Platform" value={platform.data?.service ?? "RedPA AI"} />
              <InfoRow label="Version" value={platform.data?.version ?? "—"} />
              <InfoRow
                label="Environment"
                value={platform.data?.environment ?? "—"}
              />
              <InfoRow
                label="Last refresh"
                value={lastUpdated || "Connecting…"}
              />
            </div>
          </section>
        </div>

        <section className="panel" id="remote-agents">
          <div className="panelTitle">
            <div>
              <p className="eyebrow">A2A NETWORK</p>
              <h2>Remote specialist agents</h2>
            </div>
            <span className="pill">
              {remoteAgents.data?.total ?? 0} configured
            </span>
          </div>

          <div className="remoteTable">
            <div className="remoteHeader">
              <span>Agent</span>
              <span>Endpoint</span>
              <span>Skills</span>
              <span>Connection</span>
            </div>

            {(remoteAgents.data?.items ?? []).map((agent) => (
              <div className="remoteRow" key={agent.name}>
                <div>
                  <strong>{agent.agent_name || agent.name}</strong>
                  <small>
                    {agent.agent_version ? `v${agent.agent_version}` : agent.name}
                  </small>
                </div>
                <code>{agent.base_url}</code>
                <div className="tagRow compact">
                  {agent.skills.slice(0, 3).map((skill) => (
                    <span className="tag" key={skill}>
                      {skill}
                    </span>
                  ))}
                  {agent.skills.length === 0 && <span className="muted">—</span>}
                </div>
                <div>
                  <span
                    className={`stateBadge ${
                      agent.connected ? "positive" : "negative"
                    }`}
                  >
                    {agent.connected ? "connected" : "offline"}
                  </span>
                  {agent.error && <small className="remoteError">{agent.error}</small>}
                </div>
              </div>
            ))}

            {!remoteAgents.loading && !remoteAgents.data?.items.length && (
              <div className="empty largeEmpty">
                No remote A2A agents are configured.
              </div>
            )}
          </div>
        </section>
      </section>

      {(selectedAgent || selectedLoading || selectedError) && (
        <div
          className="drawerBackdrop"
          onClick={() => {
            setSelectedAgent(null);
            setSelectedError(null);
          }}
        >
          <aside className="drawer" onClick={(event) => event.stopPropagation()}>
            <div className="drawerTop">
              <div>
                <p className="eyebrow">AGENT CARD</p>
                <h2>{selectedAgent?.name ?? "Loading agent…"}</h2>
              </div>
              <button
                className="closeButton"
                onClick={() => {
                  setSelectedAgent(null);
                  setSelectedError(null);
                }}
              >
                ×
              </button>
            </div>

            {selectedLoading && <div className="empty">Loading Agent Card…</div>}
            {selectedError && <div className="inlineError">{selectedError}</div>}

            {selectedAgent && !selectedLoading && (
              <>
                <div className="drawerSummary">
                  <span className={`stateBadge ${statusClass(selectedAgent.status)}`}>
                    {selectedAgent.status}
                  </span>
                  <code>{selectedAgent.id}</code>
                  <span>v{selectedAgent.version}</span>
                </div>

                <p className="drawerDescription">{selectedAgent.description}</p>

                <h3>Capabilities</h3>
                <div className="capabilityList">
                  {selectedAgent.capabilities.map((capability) => (
                    <article key={capability.name}>
                      <strong>{capability.name}</strong>
                      <p>{capability.description}</p>
                      <div className="tagRow">
                        {capability.tags.map((tag) => (
                          <span className="tag" key={tag}>
                            {tag}
                          </span>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>

                <h3>Supported routes</h3>
                <div className="tagRow">
                  {selectedAgent.supported_routes.map((route) => (
                    <span className="tag" key={route}>
                      {route}
                    </span>
                  ))}
                  {selectedAgent.supported_routes.length === 0 && (
                    <span className="muted">No explicit routes</span>
                  )}
                </div>

                {selectedAgent.endpoint && (
                  <>
                    <h3>Endpoint</h3>
                    <div className="endpointBox">
                      <code>{selectedAgent.endpoint.url}</code>
                      <span>{selectedAgent.endpoint.transport}</span>
                    </div>
                  </>
                )}
              </>
            )}
          </aside>
        </div>
      )}
    </main>
  );
}

function RuntimeMetric({
  label,
  value,
  total,
  kind,
}: {
  label: string;
  value: number;
  total: number;
  kind: "active" | "degraded" | "offline";
}) {
  const percent = total ? Math.min(100, (value / total) * 100) : 0;

  return (
    <div className="runtimeMetric">
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <div className="bar">
        <span
          className={`barFill ${kind}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="infoRow">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
