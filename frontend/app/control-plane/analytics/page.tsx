"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import { redpaFetch } from "@/lib/control-plane/api";

type Catalog = { metrics: string[]; dimensions: string[] };
type Group = { dimensions: Record<string,string>; value: number; event_count: number; total_weight: number };
type QueryResult = { metric: string; aggregation: string; groups: Group[]; total_groups: number };

export default function AnalyticsPage() {
  const [catalog,setCatalog]=useState<Catalog>({metrics:[],dimensions:[]});
  const [metric,setMetric]=useState("research.quality");
  const [aggregation,setAggregation]=useState("avg");
  const [groupBy,setGroupBy]=useState("");
  const [result,setResult]=useState<QueryResult|null>(null);
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);

  async function loadCatalog(){
    try { setCatalog(await redpaFetch<Catalog>("/api/v1/analytics/catalog")); } catch {}
  }
  useEffect(()=>{void loadCatalog()},[]);

  async function seed(){
    setError("");
    try {
      await redpaFetch("/api/v1/analytics/events",{method:"POST",body:JSON.stringify({items:[
        {metric:"research.quality",value:0.91,weight:1,dimensions:{workspace:"demo",agent:"research"}},
        {metric:"research.quality",value:0.97,weight:2,dimensions:{workspace:"demo",agent:"research"}},
        {metric:"research.quality",value:0.88,weight:1,dimensions:{workspace:"enterprise",agent:"research"}},
        {metric:"workflow.latency_ms",value:820,weight:1,dimensions:{workspace:"demo",agent:"planner"}},
      ]})});
      await loadCatalog();
    } catch(err){setError(err instanceof Error?err.message:"Failed to ingest demo events")}
  }

  async function runQuery(){
    setLoading(true);setError("");
    try {
      setResult(await redpaFetch<QueryResult>("/api/v1/analytics/query",{method:"POST",body:JSON.stringify({
        metric,aggregation,group_by:groupBy.trim()?[groupBy.trim()]:[],filters:{}
      })}));
    } catch(err){setError(err instanceof Error?err.message:"KPI query failed")} finally {setLoading(false)}
  }

  const totalEvents=useMemo(()=>result?.groups.reduce((a,b)=>a+b.event_count,0)??0,[result]);
  return <>
    <header className="cpHeader"><div><p className="cpEyebrow">REDPA AI · V8</p><h1>Analytics & KPI Platform</h1><p>Ingest metric facts, slice them by JSON dimensions, and calculate sum, average, weighted-average, count, min, or max KPIs.</p></div><button onClick={()=>void seed()}>Load demo facts</button></header>
    {error?<div className="cpNotice">{error}</div>:null}
    <section className="cpMetrics"><MetricCard label="Metrics" value={catalog.metrics.length}/><MetricCard label="Dimensions" value={catalog.dimensions.length}/><MetricCard label="Result groups" value={result?.total_groups??0}/><MetricCard label="Events queried" value={totalEvents}/></section>
    <section className="cpPanel"><div className="cpPanelHead"><div><span>Semantic query</span><h2>KPI explorer</h2></div></div>
      <div className="cpReliabilityForm">
        <label><span>Metric</span><input list="metric-list" value={metric} onChange={e=>setMetric(e.target.value)}/><datalist id="metric-list">{catalog.metrics.map(x=><option key={x} value={x}/>)}</datalist></label>
        <label><span>Aggregation</span><select value={aggregation} onChange={e=>setAggregation(e.target.value)}>{["sum","avg","weighted_avg","count","min","max"].map(x=><option key={x}>{x}</option>)}</select></label>
        <label><span>Group by</span><input list="dimension-list" value={groupBy} onChange={e=>setGroupBy(e.target.value)} placeholder="workspace"/><datalist id="dimension-list">{catalog.dimensions.map(x=><option key={x} value={x}/>)}</datalist></label>
      </div><div className="cpActions"><button onClick={()=>void runQuery()} disabled={loading||!metric}>{loading?"Querying…":"Run KPI query"}</button></div>
    </section>
    {result?<section className="cpPanel"><div className="cpPanelHead"><div><span>{result.aggregation}</span><h2>{result.metric}</h2></div><span>{result.total_groups} groups</span></div><div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Dimensions</th><th>Value</th><th>Events</th><th>Total weight</th></tr></thead><tbody>{result.groups.map((g,i)=><tr key={i}><td><strong>{Object.entries(g.dimensions).map(([k,v])=>`${k}=${v}`).join(" · ")||"all"}</strong></td><td>{g.value.toFixed(3)}</td><td>{g.event_count}</td><td>{g.total_weight.toFixed(2)}</td></tr>)}</tbody></table></div></section>:null}
  </>;
}
