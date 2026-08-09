"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

type Tenant = {
  id: string;
  name: string;
  slug: string;
  role: string;
  created_at: string;
};

const API =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export default function AccessControlCenter() {
  const [token, setToken] = useState("");
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [oauthProviders, setOauthProviders] = useState<string[]>([]);
  const [name, setName] = useState("RedPA Workspace");
  const [message, setMessage] = useState("");

  useEffect(() => {
    setToken(localStorage.getItem("redpa_access_token") ?? "");
  }, []);

  const request = useCallback(
    async <T,>(path: string, init?: RequestInit): Promise<T> => {
      const headers = new Headers(init?.headers ?? {});
      if (token) headers.set("Authorization", `Bearer ${token}`);

      const response = await fetch(`${API}${path}`, {
        ...init,
        headers,
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      return response.json() as Promise<T>;
    },
    [token],
  );

  const reload = useCallback(async () => {
    if (!token) return;

    try {
      const [tenantData, providerData] = await Promise.all([
        request<Tenant[]>("/tenants"),
        request<string[]>("/oauth/providers"),
      ]);
      setTenants(tenantData);
      setOauthProviders(providerData);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Load failed.");
    }
  }, [request, token]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function createTenant(event: FormEvent) {
    event.preventDefault();

    try {
      await request<Tenant>("/tenants", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      await reload();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Create failed.");
    }
  }

  async function startOAuth(provider: string) {
    try {
      const response = await request<{
        authorization_url: string;
      }>(`/oauth/${provider}/authorize`);

      window.location.assign(response.authorization_url);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "OAuth failed.");
    }
  }

  return (
    <main className="accessPage">
      <section className="accessHero">
        <p className="eyebrow">PHASE 16</p>
        <h1>Access & Tenancy Control Center</h1>
        <p>
          Manage workspaces, tenant roles, and configured OAuth providers.
        </p>
      </section>

      {message ? <div className="accessNotice">{message}</div> : null}

      {!token ? (
        <section className="accessPanel">
          Sign in through the main RedPA Control Center first.
        </section>
      ) : (
        <>
          <section className="accessMetrics">
            <article>
              <span>Tenants</span>
              <strong>{tenants.length}</strong>
            </article>
            <article>
              <span>OAuth providers</span>
              <strong>{oauthProviders.length}</strong>
            </article>
          </section>

          <section className="accessPanel">
            <h2>Create tenant</h2>
            <form onSubmit={createTenant} className="accessForm">
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
              <button type="submit">Create workspace</button>
            </form>
          </section>

          <section className="accessPanel">
            <h2>Your tenants</h2>
            <div className="accessCards">
              {tenants.map((tenant) => (
                <article key={tenant.id}>
                  <strong>{tenant.name}</strong>
                  <span>{tenant.slug}</span>
                  <code>{tenant.role}</code>
                </article>
              ))}
              {tenants.length === 0 ? <p>No tenant yet.</p> : null}
            </div>
          </section>

          <section className="accessPanel">
            <h2>OAuth providers</h2>
            {oauthProviders.length === 0 ? (
              <p>
                No OAuth provider is configured. Set provider client IDs in the
                backend environment to enable discovery.
              </p>
            ) : (
              <div className="accessCards">
                {oauthProviders.map((provider) => (
                  <article key={provider}>
                    <strong>{provider}</strong>
                    <button onClick={() => void startOAuth(provider)}>
                      Continue with {provider}
                    </button>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}
