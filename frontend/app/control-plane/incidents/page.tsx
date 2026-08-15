"use client";

import { useEffect, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Incident = {
  id:string; service:string; summary:string; severity:string; status:string; source:string;
  diagnosis:Record<string,unknown>; created_at:string; updated_at:string;
};

export default function IncidentsPage(){
  const [items,setItems]=useState<Incident[]>([]);
  const [service,setService]=useState("redpa-backend");
  const [summary,setSummary]=useState("Backend health degradation detected");
  const [error,setError]=useState("");
  async function load(){
    try{setItems(await redpaFetch<Incident[]>("/api/v1/operations/v9/incidents"));setError("");}
    catch(e){setError(e instanceof Error?e.message:"Failed to load incidents");}
  }
  async function create(){
    await redpaFetch("/api/v1/operations/v9/incidents",{method:"POST",body:JSON.stringify({service,summary,severity:"warning",source:"control-plane",metadata:{}})});
    await load();
  }
  async function diagnose(id:string){
    await redpaFetch(`/api/v1/operations/v9/incidents/${id}/diagnose`,{method:"POST"}); await load();
  }
  async function remediate(id:string){
    await redpaFetch(`/api/v1/operations/v9/incidents/${id}/remediate`,{method:"POST",body:JSON.stringify({action:"restart_container",approved:true,reason:"Operator approved restart from V9 Control Plane"})}); await load();
  }
  useEffect(()=>{void load();},[]);
  const critical=items.filter(x=>x.severity==="critical"&&x.status!=="resolved").length;
  return <>
    <header className="cpHeader"><div><p className="cpEyebrow">REDPA AI · V9</p><h1>Incident & Autonomous Operations</h1><p>Persist incidents, diagnose Docker services, and execute explicitly approved remediation through the V9 Ops Agent.</p></div><button onClick={()=>void load()}>Refresh</button></header>
    {error?<div className="cpNotice">{error}</div>:null}
    <section className="cpMetrics"><MetricCard label="Incidents" value={items.length}/><MetricCard label="Open critical" value={critical}/><MetricCard label="Resolved" value={items.filter(x=>x.status==="resolved").length}/><MetricCard label="Automation mode" value="HITL"/></section>
    <section className="cpPanel"><div className="cpPanelHead"><div><span>New incident</span><h2>Create operations incident</h2></div></div><div className="cpResearchForm"><label><span>Container service</span><input value={service} onChange={e=>setService(e.target.value)}/></label><label className="wide"><span>Summary</span><input value={summary} onChange={e=>setSummary(e.target.value)}/></label></div><div className="cpActions"><button onClick={()=>void create()}>Create incident</button></div></section>
    <section className="cpPanel"><div className="cpPanelHead"><div><span>Response queue</span><h2>Incidents</h2></div><span>{items.length} persisted</span></div><div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Service</th><th>Severity</th><th>Status</th><th>Diagnosis</th><th>Actions</th></tr></thead><tbody>{items.map(x=><tr key={x.id}><td><strong>{x.service}</strong><small>{x.summary}</small></td><td>{x.severity}</td><td><StatusBadge value={x.status}/></td><td><small>{Object.keys(x.diagnosis||{}).length?JSON.stringify(x.diagnosis):"Not diagnosed"}</small></td><td><div className="cpActions"><button className="cpLinkButton" onClick={()=>void diagnose(x.id)}>Diagnose</button><button className="cpLinkButton" onClick={()=>void remediate(x.id)} disabled={x.status==="resolved"}>Approve restart</button></div></td></tr>)}</tbody></table></div></section>
  </>;
}
