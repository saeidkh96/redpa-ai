"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type ProviderDescriptor = {
  name: string;
  provider_type: string;
  default_model: string;
  capabilities: string[];
  enabled: boolean;
};

type ProviderHealth = {
  provider: string;
  available: boolean;
  models: string[];
  detail?: string | null;
};

type Circuit = {
  provider: string;
  state: string;
  failures: number;
  failure_threshold: number;
  recovery_timeout_seconds: number;
};

type RouteResponse = {
  provider: string;
  model?: string | null;
  reason: string;
  fallback_providers: string[];
};

type Usage = {
  input_tokens?: number | null;
  output_tokens?: number | null;
  total_tokens?: number | null;
};

type InvokeResponse = {
  provider: string;
  model: string;
  content: string;
  finish_reason?: string | null;
  usage?: Usage | null;
  route: RouteResponse;
  attempted_providers: string[];
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const DEFAULT_ROUTE = {
  agent_id: "research-agent",
  capability: "chat",
};

const DEFAULT_INVOKE = {
  messages: [
    {
      role: "user",
      content: "Reply with exactly: RedPA gateway works",
    },
  ],
  agent_id: "research-agent",
  capability: "chat",
  temperature: 0,
};

export default function ModelGatewayDashboard() {
  const [providers, setProviders] = useState<ProviderDescriptor[]>([]);
  const [health, setHealth] = useState<ProviderHealth[]>([]);
  const [circuits, setCircuits] = useState<Circuit[]>([]);

  const [routePayload, setRoutePayload] = useState(
    JSON.stringify(DEFAULT_ROUTE, null, 2),
  );

  const [invokePayload, setInvokePayload] = useState(
    JSON.stringify(DEFAULT_INVOKE, null, 2),
  );

  const [routeResult, setRouteResult] = useState<RouteResponse | null>(null);

  const [invokeResult, setInvokeResult] =
    useState<InvokeResponse | null>(null);

  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  const [token, setToken] = useState("");
  const [authReady, setAuthReady] = useState(false);

  const availableProviders = useMemo(
    () => health.filter((item) => item.available).length,
    [health],
  );

  const modelCount = useMemo(
    () =>
      new Set(
        health.flatMap((item) => item.models),
      ).size,
    [health],
  );

  useEffect(() => {
    const savedToken = localStorage.getItem("redpa_access_token");

    if (savedToken) {
      setToken(savedToken);
    }

    setAuthReady(true);
  }, []);

  async function apiFetch(
    path: string,
    init?: RequestInit,
  ): Promise<Response> {
    const headers = new Headers(init?.headers);

    headers.set("Content-Type", "application/json");

    if (token) {
      headers.set(
        "Authorization",
        `Bearer ${token}`,
      );
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
    });

    if (!response.ok) {
      const text = await response.text();

      if (response.status === 401) {
        throw new Error(
          "Authentication required. Sign in from the RedPA Control Center first.",
        );
      }

      throw new Error(
        `${path}: HTTP ${response.status} ${text}`,
      );
    }

    return response;
  }

  async function load() {
    if (!token) {
      setProviders([]);
      setHealth([]);
      setCircuits([]);

      setNotice(
        "Sign in from the RedPA Control Center to access the Model Gateway.",
      );

      return;
    }

    setLoading(true);
    setNotice("");

    try {
      const [
        providersResponse,
        healthResponse,
        circuitsResponse,
      ] = await Promise.all([
        apiFetch("/model-gateway/providers"),
        apiFetch("/model-gateway/health"),
        apiFetch("/model-gateway/circuits"),
      ]);

      const providerPayload =
        (await providersResponse.json()) as ProviderDescriptor[];

      const healthPayload =
        (await healthResponse.json()) as ProviderHealth[];

      const circuitPayload =
        (await circuitsResponse.json()) as Circuit[];

      setProviders(providerPayload);
      setHealth(healthPayload);
      setCircuits(circuitPayload);
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : "Could not load Model Gateway state.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function previewRoute(
    event: FormEvent,
  ) {
    event.preventDefault();

    if (!token) {
      setNotice(
        "Authentication required. Sign in from the RedPA Control Center first.",
      );

      return;
    }

    setLoading(true);
    setNotice("");
    setRouteResult(null);

    try {
      const body = JSON.parse(routePayload);

      const response = await apiFetch(
        "/model-gateway/route",
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      );

      const result =
        (await response.json()) as RouteResponse;

      setRouteResult(result);
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : "Routing preview failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function invoke(
    event: FormEvent,
  ) {
    event.preventDefault();

    if (!token) {
      setNotice(
        "Authentication required. Sign in from the RedPA Control Center first.",
      );

      return;
    }

    setLoading(true);
    setNotice("");
    setInvokeResult(null);

    try {
      const body = JSON.parse(invokePayload);

      const response = await apiFetch(
        "/model-gateway/invoke",
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      );

      const result =
        (await response.json()) as InvokeResponse;

      setInvokeResult(result);

      await load();
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : "Model invocation failed.",
      );

      setLoading(false);
    }
  }

  function clearAuthentication() {
    localStorage.removeItem(
      "redpa_access_token",
    );

    setToken("");
    setProviders([]);
    setHealth([]);
    setCircuits([]);
    setRouteResult(null);
    setInvokeResult(null);

    setNotice(
      "Authentication cleared. Sign in again from the RedPA Control Center.",
    );
  }

  useEffect(() => {
    if (!authReady) {
      return;
    }

    if (token) {
      void load();
    } else {
      setNotice(
        "Sign in from the RedPA Control Center to access the Model Gateway.",
      );
    }
  }, [authReady, token]);

  return (
    <main className="gateway-shell">
      <section className="gateway-hero">
        <div>
          <div className="gateway-kicker">
            PHASE 12.7
          </div>

          <h1>
            Model Gateway Control Center
          </h1>

          <p>
            Inspect providers, model health,
            routing decisions, fallback state,
            circuit breakers, and live model
            invocation.
          </p>
        </div>

        <div className="gateway-chip-row">
          {token ? (
            <>
              <span className="gateway-chip">
                Authenticated
              </span>

              <button
                onClick={() => void load()}
                disabled={loading}
              >
                {loading
                  ? "Loading..."
                  : "Reload"}
              </button>

              <button
                onClick={clearAuthentication}
                disabled={loading}
              >
                Sign out
              </button>
            </>
          ) : (
            <span className="gateway-chip">
              Authentication required
            </span>
          )}
        </div>
      </section>

      {notice ? (
        <div className="gateway-notice">
          {notice}
        </div>
      ) : null}

      <section className="gateway-stats">
        <article>
          <span>Providers</span>
          <strong>
            {providers.length}
          </strong>
        </article>

        <article>
          <span>Available</span>
          <strong>
            {availableProviders}
          </strong>
        </article>

        <article>
          <span>Models</span>
          <strong>
            {modelCount}
          </strong>
        </article>

        <article>
          <span>Open circuits</span>
          <strong>
            {
              circuits.filter(
                (item) =>
                  item.state === "open",
              ).length
            }
          </strong>
        </article>
      </section>

      <section className="gateway-grid">
        <div className="gateway-panel">
          <h2>
            Providers
          </h2>

          {!token ? (
            <p>
              Protected provider data is available
              after authentication.
            </p>
          ) : providers.length === 0 ? (
            <p>
              No providers are currently registered.
            </p>
          ) : (
            <div className="gateway-card-list">
              {providers.map(
                (provider) => {
                  const providerHealth =
                    health.find(
                      (item) =>
                        item.provider ===
                        provider.name,
                    );

                  return (
                    <article
                      className="gateway-card"
                      key={provider.name}
                    >
                      <div className="gateway-card-head">
                        <div>
                          <strong>
                            {provider.name}
                          </strong>

                          <span>
                            {
                              provider.provider_type
                            }
                          </span>
                        </div>

                        <span>
                          {providerHealth?.available
                            ? "healthy"
                            : "unavailable"}
                        </span>
                      </div>

                      <p>
                        Default model:{" "}
                        {
                          provider.default_model
                        }
                      </p>

                      <div className="gateway-chip-row">
                        {provider.capabilities.map(
                          (capability) => (
                            <span
                              className="gateway-chip"
                              key={capability}
                            >
                              {capability}
                            </span>
                          ),
                        )}
                      </div>

                      {providerHealth
                        ?.models?.length ? (
                        <div className="gateway-models">
                          <span>
                            Models:
                          </span>

                          {providerHealth.models.map(
                            (model) => (
                              <code
                                key={model}
                              >
                                {model}
                              </code>
                            ),
                          )}
                        </div>
                      ) : null}

                      {providerHealth?.detail ? (
                        <pre>
                          {
                            providerHealth.detail
                          }
                        </pre>
                      ) : null}
                    </article>
                  );
                },
              )}
            </div>
          )}

          <h2 className="gateway-section-title">
            Circuit breakers
          </h2>

          {!token ? (
            <p>
              Circuit state is protected by JWT
              authentication.
            </p>
          ) : circuits.length === 0 ? (
            <p>
              No provider circuit state recorded yet.
            </p>
          ) : (
            <div className="gateway-card-list">
              {circuits.map(
                (circuit) => (
                  <article
                    className="gateway-card"
                    key={circuit.provider}
                  >
                    <div className="gateway-card-head">
                      <strong>
                        {circuit.provider}
                      </strong>

                      <span>
                        {circuit.state}
                      </span>
                    </div>

                    <p>
                      Failures{" "}
                      {circuit.failures}/
                      {
                        circuit.failure_threshold
                      }
                      {" · "}
                      Recovery{" "}
                      {
                        circuit.recovery_timeout_seconds
                      }
                      s
                    </p>
                  </article>
                ),
              )}
            </div>
          )}
        </div>

        <div className="gateway-column">
          <form
            className="gateway-panel"
            onSubmit={previewRoute}
          >
            <h2>
              Routing preview
            </h2>

            <textarea
              rows={10}
              spellCheck={false}
              value={routePayload}
              onChange={(event) =>
                setRoutePayload(
                  event.target.value,
                )
              }
            />

            <button
              disabled={
                loading || !token
              }
              type="submit"
            >
              Preview route
            </button>

            {routeResult ? (
              <pre className="gateway-result">
                {JSON.stringify(
                  routeResult,
                  null,
                  2,
                )}
              </pre>
            ) : null}
          </form>

          <form
            className="gateway-panel"
            onSubmit={invoke}
          >
            <h2>
              Invoke model
            </h2>

            <textarea
              rows={16}
              spellCheck={false}
              value={invokePayload}
              onChange={(event) =>
                setInvokePayload(
                  event.target.value,
                )
              }
            />

            <button
              disabled={
                loading || !token
              }
              type="submit"
            >
              Invoke
            </button>

            {invokeResult ? (
              <div className="gateway-result-block">
                <div className="gateway-card-head">
                  <strong>
                    {
                      invokeResult.provider
                    }{" "}
                    /{" "}
                    {
                      invokeResult.model
                    }
                  </strong>

                  <span>
                    {
                      invokeResult.finish_reason ??
                      "—"
                    }
                  </span>
                </div>

                <p>
                  {
                    invokeResult.content
                  }
                </p>

                <pre className="gateway-result">
                  {JSON.stringify(
                    {
                      usage:
                        invokeResult.usage,

                      route:
                        invokeResult.route,

                      attempted_providers:
                        invokeResult.attempted_providers,
                    },
                    null,
                    2,
                  )}
                </pre>
              </div>
            ) : null}
          </form>
        </div>
      </section>
    </main>
  );
}