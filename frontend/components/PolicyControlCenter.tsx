"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type AuditEvent = {
  id: string;
  user_id?: string | null;
  conversation_id?: string | null;
  review_id?: string | null;
  boundary: string;
  action: string;
  resource?: string | null;
  decision: "ALLOW" | "REVIEW" | "DENY" | string;
  risk: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  reason: string;
  matched_rules: string[];
  policy_version: string;
  source: string;
  event_metadata?: Record<string, unknown>;
  created_at: string;
};

type EnforcementResponse = {
  decision: string;
  risk: string;
  reason: string;
  matched_rules: string[];
  policy_version: string;
  source: string;
  executable: boolean;
  review_id?: string | null;
};

const API =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

function count(events: AuditEvent[], decision: string) {
  return events.filter((event) => event.decision === decision).length;
}

export default function PolicyControlCenter() {
  const [token, setToken] = useState("");
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [action, setAction] = useState("list_containers");
  const [boundary, setBoundary] = useState("mcp");
  const [resource, setResource] = useState("mcp_tool");
  const [argumentsText, setArgumentsText] = useState("{}");
  const [result, setResult] = useState<EnforcementResponse | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem("redpa_access_token") ?? "";
    setToken(saved);
  }, []);

  const request = useCallback(
    async <T,>(path: string, init?: RequestInit): Promise<T> => {
      const headers = new Headers(init?.headers ?? {});
      headers.set("Accept", "application/json");
      if (token) headers.set("Authorization", `Bearer ${token}`);

      const response = await fetch(`${API}${path}`, {
        ...init,
        headers,
        cache: "no-store",
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status} ${text}`);
      }

      return response.json() as Promise<T>;
    },
    [token],
  );

  const reload = useCallback(async () => {
    if (!token) {
      setLoading(false);
      setEvents([]);
      return;
    }

    setLoading(true);
    setError("");
    try {
      const data = await request<AuditEvent[]>("/policy/audit?limit=200");
      setEvents(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load policy audit.");
    } finally {
      setLoading(false);
    }
  }, [request, token]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const summary = useMemo(
    () => ({
      total: events.length,
      allow: count(events, "ALLOW"),
      review: count(events, "REVIEW"),
      deny: count(events, "DENY"),
      critical: events.filter((event) => event.risk === "CRITICAL").length,
    }),
    [events],
  );

  async function preview() {
    setError("");
    setResult(null);

    try {
      const parsedArguments = JSON.parse(argumentsText || "{}");
      const data = await request<EnforcementResponse>("/policy/enforce", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action,
          boundary,
          resource,
          arguments: parsedArguments,
        }),
      });
      setResult(data);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Policy evaluation failed.");
    }
  }

  if (!token) {
    return (
      <main className="policyPage">
        <section className="policyHero">
          <p className="eyebrow">PHASE 13.7</p>
          <h1>Policy Control Center</h1>
          <p>
            Sign in through the RedPA Control Center first. This page uses the
            same protected access token stored by the platform.
          </p>
        </section>
      </main>
    );
  }

  return (
    <main className="policyPage">
      <section className="policyHero">
        <div>
          <p className="eyebrow">PHASE 13.7</p>
          <h1>Policy Control Center</h1>
          <p>
            Inspect policy decisions, risk, matched rules, human-review links,
            and enforcement history.
          </p>
        </div>
        <button className="policyButton" onClick={() => void reload()}>
          Reload
        </button>
      </section>

      {error && <div className="policyError">{error}</div>}

      <section className="policyMetrics">
        <article><span>Events</span><strong>{summary.total}</strong></article>
        <article><span>Allowed</span><strong>{summary.allow}</strong></article>
        <article><span>Review</span><strong>{summary.review}</strong></article>
        <article><span>Denied</span><strong>{summary.deny}</strong></article>
        <article><span>Critical</span><strong>{summary.critical}</strong></article>
      </section>

      <section className="policyPanel">
        <div className="policyPanelTitle">
          <div>
            <p className="eyebrow">LIVE POLICY ENGINE</p>
            <h2>Enforcement preview</h2>
          </div>
        </div>

        <div className="policyForm">
          <label>
            Action
            <input value={action} onChange={(e) => setAction(e.target.value)} />
          </label>
          <label>
            Boundary
            <select value={boundary} onChange={(e) => setBoundary(e.target.value)}>
              <option value="mcp">MCP</option>
              <option value="internal_tool">Internal tool</option>
              <option value="workflow">Workflow</option>
            </select>
          </label>
          <label>
            Resource
            <input
              value={resource}
              onChange={(e) => setResource(e.target.value)}
            />
          </label>
          <label className="policyWide">
            Arguments JSON
            <textarea
              rows={5}
              value={argumentsText}
              onChange={(e) => setArgumentsText(e.target.value)}
            />
          </label>
        </div>

        <button className="policyButton" onClick={() => void preview()}>
          Evaluate
        </button>

        {result && (
          <div className="policyResult">
            <div>
              <strong>{result.decision}</strong>
              <span>{result.risk}</span>
              <span>{result.executable ? "Executable" : "Blocked"}</span>
            </div>
            <p>{result.reason}</p>
            <code>{result.matched_rules.join(", ") || "No matched rule"}</code>
            {result.review_id && <p>Human Review: {result.review_id}</p>}
          </div>
        )}
      </section>

      <section className="policyPanel">
        <div className="policyPanelTitle">
          <div>
            <p className="eyebrow">AUDIT TRAIL</p>
            <h2>Policy events</h2>
          </div>
          <span>{loading ? "Loading..." : `${events.length} events`}</span>
        </div>

        <div className="policyTableWrap">
          <table className="policyTable">
            <thead>
              <tr>
                <th>Time</th>
                <th>Action</th>
                <th>Decision</th>
                <th>Risk</th>
                <th>Boundary</th>
                <th>Rule</th>
                <th>Review</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td>{new Date(event.created_at).toLocaleString()}</td>
                  <td><code>{event.action}</code></td>
                  <td>
                    <span className={`decision decision-${event.decision.toLowerCase()}`}>
                      {event.decision}
                    </span>
                  </td>
                  <td>{event.risk}</td>
                  <td>{event.boundary}</td>
                  <td>{event.matched_rules.join(", ")}</td>
                  <td>{event.review_id ?? "—"}</td>
                </tr>
              ))}
              {!loading && events.length === 0 && (
                <tr>
                  <td colSpan={7}>No policy events recorded yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
