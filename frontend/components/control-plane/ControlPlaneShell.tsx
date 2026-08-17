"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

const nav = [
  ["Overview", "/control-plane"],
  ["Agents", "/control-plane/agents"],
  ["Research", "/control-plane/research"],
  ["Analytics", "/control-plane/analytics"],
  ["Connectors", "/control-plane/connectors"],
  ["Cloud & SLO", "/control-plane/operations"],
  ["Incidents", "/control-plane/incidents"],
  ["Release Gate", "/control-plane/cloud"],
  ["Cloud Cost", "/control-plane/cost"],
  ["Models", "/control-plane/models"],
  ["Tools & MCP", "/control-plane/tools"],
  ["Workflows", "/control-plane/workflows"],
  ["Executions", "/control-plane/executions"],
  ["Eval & Reliability", "/control-plane/reliability"],
  ["Memory", "/control-plane/memory"],
  ["Usage & Cost", "/control-plane/usage"],
  ["Human Reviews", "/control-plane/reviews"],
  ["Governance Runs", "/control-plane/governance"],
  ["Policy Management", "/control-plane/policy"],
  ["Platform Evolution", "/control-plane/evolution"],
  ["Access & Tenancy", "/control-plane/access"],
  ["Evaluations", "/evaluations"],
  ["Events", "/events"],
  ["Legacy Ops", "/"],
] as const;

export default function ControlPlaneShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="cpShell">
      <aside className="cpSidebar">
        <Link href="/control-plane" className="cpBrand">
          <img src="/logo.png" alt="RedPA AI" />
          <div><strong>RedPA AI</strong><span>V18 Enterprise Agent Platform</span></div>
        </Link>
        <nav className="cpNav">
          {nav.map(([label, href]) => {
            const active = href === "/control-plane" ? pathname === href : pathname.startsWith(href);
            return <Link key={href} href={href} className={active ? "active" : ""}>{label}</Link>;
          })}
        </nav>
        <div className="cpSidebarFoot">
          <span className="cpDot" />
          <div><strong>Control Plane</strong><small>API-backed views only</small></div>
        </div>
      </aside>
      <main className="cpMain">{children}</main>
    </div>
  );
}
