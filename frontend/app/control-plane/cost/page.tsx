"use client";
import { useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import { redpaFetch } from "@/lib/control-plane/api";

type Estimate={backend_eur:number;workers_eur:number;data_services_eur:number;observability_eur:number;other_eur:number;monthly_total_eur:number;annual_total_eur:number};
export default function CostPage(){
 const [estimate,setEstimate]=useState<Estimate|null>(null);
 async function run(){setEstimate(await redpaFetch<Estimate>("/api/v1/operations/v9/cost/estimate",{method:"POST",body:JSON.stringify({backend_replicas:2,worker_replicas:2,monthly_backend_replica_eur:55,monthly_worker_replica_eur:40,managed_data_services_eur:180,observability_eur:45,other_eur:25})}));}
 return <><header className="cpHeader"><div><p className="cpEyebrow">REDPA AI · V9</p><h1>Cloud Cost Model</h1><p>Estimate application, worker, managed data, and observability spend before changing capacity.</p></div><button onClick={()=>void run()}>Estimate demo cost</button></header><section className="cpMetrics"><MetricCard label="Monthly" value={estimate?`€${estimate.monthly_total_eur.toFixed(2)}`:"—"}/><MetricCard label="Annual" value={estimate?`€${estimate.annual_total_eur.toFixed(2)}`:"—"}/><MetricCard label="Backend" value={estimate?`€${estimate.backend_eur.toFixed(2)}`:"—"}/><MetricCard label="Workers" value={estimate?`€${estimate.workers_eur.toFixed(2)}`:"—"}/></section>{estimate?<section className="cpPanel"><pre className="cpResponse">{JSON.stringify(estimate,null,2)}</pre></section>:null}</>;
}
