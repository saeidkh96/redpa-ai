"use client";

import { FormEvent, useEffect, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Tenant = {
  id: string;
  name: string;
  slug: string;
  role: string;
  created_at: string;
};

export default function AccessPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [oauthProviders, setOauthProviders] = useState<string[]>([]);
  const [name, setName] = useState("RedPA Workspace");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    const [tenantResult, providerResult] = await Promise.allSettled([
      redpaFetch<Tenant[]>("/api/v1/tenants", {}, true),
      redpaFetch<string[]>("/api/v1/oauth/providers", {}, true),
    ]);
    if (tenantResult.status === "fulfilled") setTenants(tenantResult.value);
    if (providerResult.status === "fulfilled") setOauthProviders(providerResult.value);
    if (tenantResult.status === "rejected" || providerResult.status === "rejected") {
      setError("A valid RedPA access token is required to load access-control data.");
    }
    setLoading(false);
  }

  useEffect(() => { void load(); }, []);

  async function createTenant(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    setError("");
    setNotice("");
    try {
      const created = await redpaFetch<Tenant>("/api/v1/tenants", {
        method: "POST",
        body: JSON.stringify({ name: name.trim() }),
      }, true);
      setNotice(`Created tenant ${created.name}.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tenant creation failed");
    } finally {
      setCreating(false);
    }
  }

  async function startOAuth(provider: string) {
    setError("");
    try {
      const response = await redpaFetch<{authorization_url: string}>(`/api/v1/oauth/${encodeURIComponent(provider)}/authorize`, {}, true);
      window.location.assign(response.authorization_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "OAuth authorization failed");
    }
  }

  return <>
    <header className="cpHeader">
      <div><p className="cpEyebrow">CONTROL PLANE / ACCESS</p><h1>Tenancy & Identity</h1><p>Manage workspaces exposed by the tenant API and inspect configured OAuth providers.</p></div>
      <button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button>
    </header>

    {notice ? <div className="cpSuccess">{notice}</div> : null}
    {error ? <div className="cpNotice">{error}</div> : null}

    <section className="cpMetrics">
      <MetricCard label="Tenants" value={tenants.length} />
      <MetricCard label="Owner workspaces" value={tenants.filter((t) => t.role === "owner").length} />
      <MetricCard label="OAuth providers" value={oauthProviders.length} />
      <MetricCard label="RBAC roles observed" value={new Set(tenants.map((t) => t.role)).size} />
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>Workspace</span><h2>Create tenant</h2></div></div>
      <form className="cpFormRow" onSubmit={createTenant}>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Workspace name" />
        <button type="submit" disabled={creating || name.trim().length < 2}>{creating ? "Creating…" : "Create workspace"}</button>
      </form>
    </section>

    <section className="cpGrid2">
      <div className="cpPanel">
        <div className="cpPanelHead"><div><span>Membership</span><h2>Your tenants</h2></div></div>
        <div className="cpRows">
          {tenants.map((tenant) => <div className="cpRow" key={tenant.id}><div><strong>{tenant.name}</strong><small>{tenant.slug} · {tenant.id}</small></div><StatusBadge value={tenant.role} /></div>)}
          {!tenants.length ? <p className="cpMuted">No tenant data is available.</p> : null}
        </div>
      </div>

      <div className="cpPanel">
        <div className="cpPanelHead"><div><span>Identity</span><h2>OAuth providers</h2></div></div>
        <div className="cpRows">
          {oauthProviders.map((provider) => <div className="cpRow" key={provider}><div><strong>{provider}</strong><small>Configured provider</small></div><button className="cpLinkButton" onClick={() => void startOAuth(provider)}>Authorize</button></div>)}
          {!oauthProviders.length ? <p className="cpMuted">No OAuth provider is configured in the backend environment.</p> : null}
        </div>
      </div>
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead"><div><span>RBAC scope</span><h2>Implemented access boundary</h2></div></div>
      <p className="cpMuted">Tenant creation, tenant listing and member assignment are implemented in the backend. Member assignment remains permission-gated by the existing RBAC authorization service; this Control Plane view does not invent a user-directory API that the backend does not expose.</p>
    </section>
  </>;
}
