"use client";

import { useEffect, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Connector={id:string;name:string;kind:string;endpoint_url:string;secret_env_var?:string|null;enabled:boolean;created_at:string};
type Delivery={id:string;status:string;attempt_count:number;response_status?:number|null;error?:string|null;dry_run:boolean};

export default function ConnectorsPage(){
 const [items,setItems]=useState<Connector[]>([]);const [name,setName]=useState("n8n demo");const [kind,setKind]=useState("n8n_webhook");const [url,setUrl]=useState("http://host.docker.internal:5678/webhook/redpa");const [selected,setSelected]=useState("");const [delivery,setDelivery]=useState<Delivery|null>(null);const [error,setError]=useState("");
 async function load(){try{setItems(await redpaFetch<Connector[]>("/api/v1/connectors?limit=100"))}catch(e){setError(e instanceof Error?e.message:"Failed to load connectors")}}
 useEffect(()=>{void load()},[]);
 async function create(){setError("");try{const item=await redpaFetch<Connector>("/api/v1/connectors",{method:"POST",body:JSON.stringify({name,kind,endpoint_url:url,enabled:true,metadata:{source:"control-plane"}})});setSelected(item.id);await load()}catch(e){setError(e instanceof Error?e.message:"Create failed")}}
 async function execute(dryRun:boolean){if(!selected)return;setError("");try{const r=await redpaFetch<{delivery:Delivery}>(`/api/v1/connectors/${selected}/execute`,{method:"POST",body:JSON.stringify({payload:{event:"redpa.v8.demo",message:"Hello from RedPA"},approval_granted:!dryRun,dry_run:dryRun})});setDelivery(r.delivery)}catch(e){setError(e instanceof Error?e.message:"Execution failed")}}
 return <><header className="cpHeader"><div><p className="cpEyebrow">REDPA AI · V8</p><h1>Enterprise Connectors & Automation</h1><p>Register outbound Webhook, Slack Webhook, GitHub Dispatch and n8n integrations with retries, secret indirection, dry-runs and approval-gated side effects.</p></div><button onClick={()=>void load()}>Refresh</button></header>{error?<div className="cpNotice">{error}</div>:null}
 <section className="cpMetrics"><MetricCard label="Connectors" value={items.length}/><MetricCard label="Enabled" value={items.filter(x=>x.enabled).length}/><MetricCard label="Kinds" value={new Set(items.map(x=>x.kind)).size}/><MetricCard label="Last delivery" value={delivery?.status??"—"}/></section>
 <section className="cpPanel"><div className="cpPanelHead"><div><span>Registry</span><h2>Create connector</h2></div></div><div className="cpReliabilityForm"><label><span>Name</span><input value={name} onChange={e=>setName(e.target.value)}/></label><label><span>Kind</span><select value={kind} onChange={e=>setKind(e.target.value)}>{["webhook","slack_webhook","github_dispatch","n8n_webhook"].map(x=><option key={x}>{x}</option>)}</select></label><label><span>Endpoint URL</span><input value={url} onChange={e=>setUrl(e.target.value)}/></label></div><div className="cpActions"><button onClick={()=>void create()}>Register connector</button></div></section>
 <section className="cpPanel"><div className="cpPanelHead"><div><span>Automation catalog</span><h2>Configured connectors</h2></div><span>{items.length} total</span></div><div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Name</th><th>Kind</th><th>Status</th><th>Endpoint</th><th></th></tr></thead><tbody>{items.map(x=><tr key={x.id}><td><strong>{x.name}</strong><small>{x.id}</small></td><td>{x.kind}</td><td><StatusBadge value={x.enabled?"enabled":"disabled"}/></td><td>{x.endpoint_url}</td><td><button className="cpLinkButton" onClick={()=>setSelected(x.id)}>Select</button></td></tr>)}</tbody></table></div></section>
 <section className="cpPanel"><div className="cpPanelHead"><div><span>Delivery</span><h2>Policy-aware execution</h2></div>{delivery?<StatusBadge value={delivery.status}/>:null}</div><p className="cpMuted">Dry-run performs no external side effect. Live execution explicitly grants approval and uses retry/backoff.</p><div className="cpActions"><button onClick={()=>void execute(true)} disabled={!selected}>Dry run</button><button onClick={()=>void execute(false)} disabled={!selected}>Approve & execute</button></div>{delivery?<div className="cpResponse"><pre>{JSON.stringify(delivery,null,2)}</pre></div>:null}</section>
 </>;
}
