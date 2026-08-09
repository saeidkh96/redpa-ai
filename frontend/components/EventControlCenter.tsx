"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type EventRow = {
  id: string;
  tenant_id?: string | null;
  event_type: string;
  aggregate_type: string;
  aggregate_id: string;
  status: string;
  attempts: number;
  last_error?: string | null;
  created_at: string;
  published_at?: string | null;
};

const API =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export default function EventControlCenter() {
  const [token, setToken] = useState("");
  const [events, setEvents] = useState<EventRow[]>([]);
  const [message, setMessage] = useState("");
  const [eventType, setEventType] = useState("redpa.demo.created");

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
      const data = await request<EventRow[]>("/events?limit=200");
      setEvents(data);
      setMessage("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Load failed.");
    }
  }, [request, token]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const summary = useMemo(
    () => ({
      total: events.length,
      pending: events.filter((e) => e.status === "pending").length,
      published: events.filter((e) => e.status === "published").length,
      failed: events.filter((e) => e.status === "failed").length,
    }),
    [events],
  );

  async function enqueue() {
    try {
      await request("/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: eventType,
          aggregate_type: "demo",
          aggregate_id: crypto.randomUUID(),
          payload: {
            message: "RedPA event-driven integration works",
          },
          metadata: {
            source: "event-control-center",
          },
        }),
      });
      await reload();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Enqueue failed.");
    }
  }

  async function flush() {
    try {
      const result = await request<{
        inspected: number;
        published: number;
        failed: number;
      }>("/events/flush", {
        method: "POST",
      });
      setMessage(
        `Inspected ${result.inspected}, published ${result.published}, failed ${result.failed}.`,
      );
      await reload();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Flush failed.");
    }
  }

  return (
    <main className="eventPage">
      <section className="eventHero">
        <div>
          <p className="eyebrow">PHASE 17</p>
          <h1>Event & Integration Control Center</h1>
          <p>
            Transactional outbox + Redis Streams for durable event-driven
            integration.
          </p>
        </div>
        <button onClick={() => void reload()}>Reload</button>
      </section>

      {message ? <div className="eventNotice">{message}</div> : null}

      {!token ? (
        <section className="eventPanel">
          Sign in through the main RedPA Control Center first.
        </section>
      ) : (
        <>
          <section className="eventMetrics">
            <article><span>Events</span><strong>{summary.total}</strong></article>
            <article><span>Pending</span><strong>{summary.pending}</strong></article>
            <article><span>Published</span><strong>{summary.published}</strong></article>
            <article><span>Failed</span><strong>{summary.failed}</strong></article>
          </section>

          <section className="eventPanel">
            <h2>Publish demo event</h2>
            <div className="eventActions">
              <input
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
              />
              <button onClick={() => void enqueue()}>Enqueue</button>
              <button onClick={() => void flush()}>Flush to Redis</button>
            </div>
          </section>

          <section className="eventPanel">
            <h2>Outbox</h2>
            <div className="eventTableWrap">
              <table className="eventTable">
                <thead>
                  <tr>
                    <th>Created</th>
                    <th>Type</th>
                    <th>Aggregate</th>
                    <th>Status</th>
                    <th>Attempts</th>
                    <th>Error</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id}>
                      <td>{new Date(event.created_at).toLocaleString()}</td>
                      <td><code>{event.event_type}</code></td>
                      <td>{event.aggregate_type}:{event.aggregate_id}</td>
                      <td>{event.status}</td>
                      <td>{event.attempts}</td>
                      <td>{event.last_error ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
