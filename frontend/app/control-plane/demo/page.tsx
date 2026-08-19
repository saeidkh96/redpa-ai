"use client";

import { useState } from "react";
import { redpaFetch } from "@/lib/control-plane/api";
import StatusBadge from "@/components/control-plane/StatusBadge";

type Stage = { stage: number; name: string; status: string; detail: string };
type DemoResult = { demo_id: string; status: string; stages: Stage[]; evidence_path?: string };

export default function ProductionDemoPage() {
  const [result, setResult] = useState<DemoResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  async function runDemo() {
    setRunning(true); setError(""); setResult(null);
    try {
      const data = await redpaFetch<DemoResult>("/api/v1/production-demo/v18.2/run", {
        method: "POST",
        body: JSON.stringify({
          task: "List the running Docker containers and return a concise runtime summary.",
          primary_agent: "research-agent",
          fallback_agent: "docker-agent",
          inject_primary_failure: true,
          approval_granted: false,
        }),
      });
      setResult(data);
    } catch (e) { setError(e instanceof Error ? e.message : "Demo failed"); }
    finally { setRunning(false); }
  }

  return <>
    <header className="cpHeader"><div><p className="cpEyebrow">REDPA AI · V18.2</p><h1>Production E2E Demo</h1><p>Reproducible failure → fallback → real A2A execution → evaluation → evidence flow.</p></div><button onClick={() => void runDemo()} disabled={running}>{running ? "Running…" : "Run E2E Demo"}</button></header>
    {error ? <div className="cpNotice">{error}</div> : null}
    <section className="cpPanel"><div className="cpPanelHead"><div><span>Execution</span><h2>{result ? `Demo ${result.demo_id}` : "Ready"}</h2></div><StatusBadge value={result?.status} /></div>
      <div className="cpRows">{result?.stages?.length ? result.stages.map((s) => <div className="cpRow" key={s.stage}><div><strong>Stage {s.stage} · {s.name}</strong><small>{s.detail}</small></div><StatusBadge value={s.status} /></div>) : <p className="cpMuted">Run the demo while the RedPA Docker stack is healthy.</p>}</div>
    </section>
    {result?.evidence_path ? <section className="cpPanel"><div className="cpPanelHead"><div><span>Evidence</span><h2>Machine-readable audit artifact</h2></div></div><p className="cpMuted">{result.evidence_path}</p></section> : null}
  </>;
}
