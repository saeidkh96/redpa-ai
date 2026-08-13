"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type MCPServer = {
  name: string;
  description?: string | null;
  transport: string;
  url: string;
  enabled: boolean;
  requires_approval: boolean;
};

type MCPServerHealth = {
  name: string;
  enabled: boolean;
  status: string;
  tool_count: number;
  latency_ms: number;
  error?: string | null;
  checked_at: string;
};

type MCPHealth = {
  status: string;
  configured_servers: number;
  enabled_servers: number;
  connected_servers: number;
  unavailable_servers: number;
  total_tools: number;
  checked_at: string;
  servers: MCPServerHealth[];
};

type UnifiedTool = {
  qualified_name: string;
  source: "internal" | "mcp";
  name: string;
  display_name?: string | null;
  description?: string | null;
  version?: string | null;
  server_name?: string | null;
  requires_approval: boolean;
  input_schema: Record<string, unknown>;
};

type ToolCatalog = {
  items: UnifiedTool[];
  total: number;
  internal_total: number;
  mcp_total: number;
  mcp_server_errors: Record<string, string>;
  refreshed_at: string;
};

type ReloadResult = { configured_servers: number; message: string };

export default function ToolsPage() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [health, setHealth] = useState<MCPHealth | null>(null);
  const [catalog, setCatalog] = useState<ToolCatalog | null>(null);
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load(refresh = false) {
    setLoading(true);
    setError("");
    try {
      const [serverList, snapshot, tools] = await Promise.all([
        redpaFetch<MCPServer[]>("/api/v1/mcp/servers", {}, true),
        redpaFetch<MCPHealth>("/api/v1/mcp/health", {}, true),
        redpaFetch<ToolCatalog>(`/api/v1/tools/catalog${refresh ? "?refresh=true" : ""}`, {}, true),
      ]);
      setServers(serverList);
      setHealth(snapshot);
      setCatalog(tools);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tools and MCP data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, []);

  async function reloadMCP() {
    setNotice("");
    setError("");
    try {
      const result = await redpaFetch<ReloadResult>("/api/v1/mcp/servers/reload", { method: "POST" }, true);
      setNotice(result.message);
      await load(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "MCP reload failed");
    }
  }

  const filteredTools = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return catalog?.items ?? [];
    return (catalog?.items ?? []).filter((tool) =>
      [tool.qualified_name, tool.name, tool.display_name, tool.description, tool.server_name, tool.source]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle)),
    );
  }, [catalog, query]);

  return <>
    <header className="cpHeader">
      <div><p className="cpEyebrow">CONTROL PLANE / TOOLS & MCP</p><h1>Tool Platform</h1><p>Unified internal and MCP tool inventory backed by the live RedPA catalog and MCP registry.</p></div>
      <div className="cpActions"><button onClick={() => void load(true)} disabled={loading}>{loading ? "Refreshing…" : "Refresh catalog"}</button><button className="cpSecondary" onClick={() => void reloadMCP()}>Reload MCP</button></div>
    </header>
    {notice ? <div className="cpSuccess">{notice}</div> : null}
    {error ? <div className="cpNotice">{error}</div> : null}

    <section className="cpMetrics">
      <MetricCard label="Unified tools" value={catalog?.total ?? "—"} hint={`${catalog?.internal_total ?? 0} internal`} />
      <MetricCard label="MCP tools" value={catalog?.mcp_total ?? "—"} hint={`${health?.total_tools ?? 0} discovered`} />
      <MetricCard label="MCP servers" value={health?.configured_servers ?? servers.length} hint={`${health?.connected_servers ?? 0} connected`} />
      <MetricCard label="MCP health" value={health?.status ?? "unknown"} hint={`${health?.unavailable_servers ?? 0} unavailable`} />
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>MCP Registry</span><h2>Configured servers</h2></div><StatusBadge value={health?.status} /></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Server</th><th>Status</th><th>Tools</th><th>Latency</th><th>Approval</th><th>Endpoint</th></tr></thead><tbody>
        {servers.map((server) => {
          const state = health?.servers.find((item) => item.name === server.name);
          return <tr key={server.name}><td><strong>{server.name}</strong><small>{server.description || server.transport}</small></td><td><StatusBadge value={state?.status || (server.enabled ? "enabled" : "disabled")} />{state?.error ? <small>{state.error}</small> : null}</td><td>{state?.tool_count ?? "—"}</td><td>{state ? `${state.latency_ms.toFixed(1)} ms` : "—"}</td><td>{server.requires_approval ? "Required" : "Not required"}</td><td><code className="cpCode">{server.url}</code></td></tr>;
        })}
      </tbody></table></div>
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Unified Catalog</span><h2>Available tools</h2></div><small className="cpMuted">{catalog?.refreshed_at ? new Date(catalog.refreshed_at).toLocaleString() : "Not loaded"}</small></div>
      <div className="cpSearch"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter by tool, server, source or description" /><button type="button" onClick={() => setQuery("")}>Clear</button></div>
      {Object.keys(catalog?.mcp_server_errors ?? {}).length ? <div className="cpNotice">{Object.entries(catalog?.mcp_server_errors ?? {}).map(([name, message]) => <div key={name}><strong>{name}:</strong> {message}</div>)}</div> : null}
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Tool</th><th>Source</th><th>Server</th><th>Approval</th><th>Description</th></tr></thead><tbody>
        {filteredTools.map((tool) => <tr key={tool.qualified_name}><td><strong>{tool.display_name || tool.name}</strong><small>{tool.qualified_name}</small></td><td><StatusBadge value={tool.source} /></td><td>{tool.server_name || "RedPA"}</td><td>{tool.requires_approval ? "Required" : "No"}</td><td>{tool.description || "—"}</td></tr>)}
      </tbody></table></div>
      {!filteredTools.length ? <p className="cpMuted">No tools match the current filter.</p> : null}
    </section>
  </>;
}
