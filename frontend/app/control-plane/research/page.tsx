"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Evidence = {
  title: string;
  url: string;
  snippet: string;
  source_domain: string;
  score: number;
};

type Quality = {
  score: number;
  coverage_score: number;
  source_diversity_score: number;
  evidence_count: number;
  unique_domains: number;
  passed: boolean;
};

type TimelineEvent = {
  id: string;
  stage: string;
  status: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

type ResearchRun = {
  id: string;
  query: string;
  status: string;
  current_stage: string;
  progress: number;
  max_results: number;
  minimum_quality_score: number;
  provider?: string | null;
  report?: string | null;
  evidence: Evidence[];
  quality?: Quality | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  timeline?: TimelineEvent[];
};

type ResearchRunList = {
  items: ResearchRun[];
  total: number;
};

export default function EnterpriseResearchPage() {
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [selected, setSelected] = useState<ResearchRun | null>(null);
  const [query, setQuery] = useState(
    "Research the current enterprise AI agent platform landscape and compare the main architectural patterns.",
  );
  const [maxResults, setMaxResults] = useState("8");
  const [minimumQuality, setMinimumQuality] = useState("0.65");
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  async function loadRuns() {
    try {
      const payload = await redpaFetch<ResearchRunList>("/api/v1/research/runs?limit=50");
      setRuns(payload.items);
      if (!selected && payload.items.length) {
        void inspect(payload.items[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load research runs");
    } finally {
      setLoading(false);
    }
  }

  async function inspect(id: string) {
    try {
      const detail = await redpaFetch<ResearchRun>(`/api/v1/research/runs/${id}`);
      setSelected(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to inspect research run");
    }
  }

  async function startResearch() {
    if (!query.trim()) return;
    setStarting(true);
    setError("");
    try {
      const run = await redpaFetch<ResearchRun>("/api/v1/research/runs", {
        method: "POST",
        body: JSON.stringify({
          query: query.trim(),
          max_results: Number(maxResults),
          minimum_quality_score: Number(minimumQuality),
        }),
      });
      setSelected(run);
      await loadRuns();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start research");
    } finally {
      setStarting(false);
    }
  }

  useEffect(() => {
    void loadRuns();
  }, []);

  useEffect(() => {
    if (!selected || !["queued", "running"].includes(selected.status)) return;
    const timer = window.setInterval(() => {
      void inspect(selected.id);
      void loadRuns();
    }, 2000);
    return () => window.clearInterval(timer);
  }, [selected?.id, selected?.status]);

  const completed = useMemo(
    () => runs.filter((run) => run.status === "completed"),
    [runs],
  );
  const avgQuality = useMemo(() => {
    const scores = completed
      .map((run) => run.quality?.score)
      .filter((score): score is number => typeof score === "number");
    return scores.length
      ? scores.reduce((sum, value) => sum + value, 0) / scores.length
      : null;
  }, [completed]);

  return <>
    <header className="cpHeader">
      <div>
        <p className="cpEyebrow">REDPA AI · V7</p>
        <h1>Enterprise Research Workspace</h1>
        <p>Run an evidence-first research workflow, watch its execution timeline live, inspect ranked sources, and review deterministic quality evidence.</p>
      </div>
      <button onClick={() => void loadRuns()} disabled={loading}>
        {loading ? "Refreshing…" : "Refresh"}
      </button>
    </header>

    {error ? <div className="cpNotice">{error}</div> : null}

    <section className="cpMetrics">
      <MetricCard label="Research runs" value={runs.length} />
      <MetricCard label="Completed" value={completed.length} />
      <MetricCard label="Running" value={runs.filter((run) => ["queued", "running"].includes(run.status)).length} />
      <MetricCard label="Average quality" value={avgQuality == null ? "—" : avgQuality.toFixed(3)} />
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead">
        <div><span>New execution</span><h2>Start enterprise research</h2></div>
      </div>
      <div className="cpResearchForm">
        <label className="wide">
          <span>Research question</span>
          <textarea value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>
        <label>
          <span>Evidence target</span>
          <input value={maxResults} onChange={(event) => setMaxResults(event.target.value)} />
        </label>
        <label>
          <span>Minimum quality</span>
          <input value={minimumQuality} onChange={(event) => setMinimumQuality(event.target.value)} />
        </label>
      </div>
      <div className="cpActions">
        <button onClick={() => void startResearch()} disabled={starting || !query.trim()}>
          {starting ? "Starting…" : "Start research"}
        </button>
      </div>
    </section>

    <section className="cpPanel">
      <div className="cpPanelHead">
        <div><span>Execution history</span><h2>Research runs</h2></div>
        <span>{runs.length} persisted</span>
      </div>
      <div className="cpTableWrap">
        <table className="cpTable">
          <thead><tr><th>Question</th><th>Status</th><th>Stage</th><th>Progress</th><th>Quality</th><th>Updated</th><th></th></tr></thead>
          <tbody>
            {runs.map((run) => <tr key={run.id}>
              <td><strong>{run.query}</strong><small>{run.id}</small></td>
              <td><StatusBadge value={run.status} /></td>
              <td>{run.current_stage}</td>
              <td>{run.progress}%</td>
              <td>{run.quality?.score.toFixed(3) ?? "—"}</td>
              <td>{new Date(run.updated_at).toLocaleString()}</td>
              <td><button className="cpLinkButton" onClick={() => void inspect(run.id)}>Inspect</button></td>
            </tr>)}
          </tbody>
        </table>
      </div>
      {!runs.length ? <p className="cpMuted">No enterprise research runs have been created yet.</p> : null}
    </section>

    {selected ? <>
      <section className="cpPanel">
        <div className="cpPanelHead">
          <div><span>Live execution</span><h2>{selected.query}</h2></div>
          <StatusBadge value={selected.status} />
        </div>
        <div className="cpProgressTrack">
          <div className="cpProgressFill" style={{ width: `${selected.progress}%` }} />
        </div>
        <div className="cpDetailGrid">
          <div><span>Stage</span><strong>{selected.current_stage}</strong></div>
          <div><span>Progress</span><strong>{selected.progress}%</strong></div>
          <div><span>Provider</span><strong>{selected.provider || "—"}</strong></div>
          <div><span>Evidence</span><strong>{selected.evidence.length}</strong></div>
        </div>
        {selected.error ? <div className="cpNotice">{selected.error}</div> : null}

        <div className="cpTimeline">
          {(selected.timeline || []).map((event) => <article key={event.id}>
            <span className="cpTimelineDot" />
            <div>
              <div className="cpResultSummary">
                <strong>{event.stage}</strong>
                <StatusBadge value={event.status} />
              </div>
              <p>{event.message}</p>
              <small>{new Date(event.created_at).toLocaleString()}</small>
            </div>
          </article>)}
        </div>
      </section>

      {selected.quality ? <section className="cpMetrics">
        <MetricCard label="Quality score" value={selected.quality.score.toFixed(3)} />
        <MetricCard label="Coverage" value={selected.quality.coverage_score.toFixed(3)} />
        <MetricCard label="Source diversity" value={selected.quality.source_diversity_score.toFixed(3)} />
        <MetricCard label="Quality gate" value={selected.quality.passed ? "PASS" : "REVIEW"} />
      </section> : null}

      <section className="cpPanel">
        <div className="cpPanelHead">
          <div><span>Evidence</span><h2>Ranked research sources</h2></div>
          <span>{selected.evidence.length} items</span>
        </div>
        <div className="cpEvidenceGrid">
          {selected.evidence.map((item, index) => <article key={`${item.url}-${index}`}>
            <div className="cpPanelHead">
              <div><span>{item.source_domain}</span><h2>{item.title}</h2></div>
              <strong>{item.score.toFixed(3)}</strong>
            </div>
            <p>{item.snippet}</p>
            <a href={item.url} target="_blank" rel="noreferrer">Open source</a>
          </article>)}
        </div>
        {!selected.evidence.length ? <p className="cpMuted">Evidence appears after the web-research stage completes.</p> : null}
      </section>

      {selected.report ? <section className="cpPanel">
        <div className="cpPanelHead"><div><span>Output</span><h2>Evidence-first report</h2></div></div>
        <div className="cpResponse"><pre>{selected.report}</pre></div>
      </section> : null}
    </> : null}
  </>;
}
