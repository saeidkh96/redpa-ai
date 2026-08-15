"use client";
import { useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import { redpaFetch } from "@/lib/control-plane/api";

type Decision={decision:string;checks:Record<string,boolean>;reasons:string[]};
export default function CloudPage(){
  const [decision,setDecision]=useState<Decision|null>(null);
  async function evaluate(){setDecision(await redpaFetch<Decision>("/api/v1/operations/v9/release/readiness",{method:"POST",body:JSON.stringify({availability:0.997,p95_latency_ms:420,availability_target:0.99,p95_latency_target_ms:1000,open_critical_incidents:0,security_gate_passed:true,regression_gate_passed:true})}));}
  return <><header className="cpHeader"><div><p className="cpEyebrow">REDPA AI · V9</p><h1>Cloud Release Readiness</h1><p>Combine SLO evidence, incident state, security, and regression gates before production promotion.</p></div><button onClick={()=>void evaluate()}>Evaluate demo candidate</button></header><section className="cpMetrics"><MetricCard label="Decision" value={decision?.decision??"—"}/><MetricCard label="Availability" value="99.7%"/><MetricCard label="p95 latency" value="420 ms"/><MetricCard label="Critical incidents" value="0"/></section>{decision?<section className="cpPanel"><div className="cpPanelHead"><div><span>Promotion gate</span><h2>{decision.decision}</h2></div></div><pre className="cpResponse">{JSON.stringify(decision.checks,null,2)}</pre>{decision.reasons.length?<p>Blocking checks: {decision.reasons.join(", ")}</p>:<p className="cpMuted">All release checks passed.</p>}</section>:null}</>;
}
