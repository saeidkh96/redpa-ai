"use client";

import { useEffect, useMemo, useState } from "react";
import MetricCard from "@/components/control-plane/MetricCard";
import StatusBadge from "@/components/control-plane/StatusBadge";
import { redpaFetch } from "@/lib/control-plane/api";

type Review = {
  id: string;
  conversation_id: string;
  user_id: string;
  message_id?: string | null;
  status: string;
  reason: string;
  requested_action?: string | null;
  request_content?: string | null;
  action_payload?: Record<string, unknown> | null;
  reviewer_feedback?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
};

type ReviewList = { items: Review[]; total: number; limit: number; offset: number };
type Filter = "all" | "pending" | "approved" | "rejected";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState<Filter>("all");
  const [selected, setSelected] = useState<Review | null>(null);
  const [feedback, setFeedback] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState("");

  async function load(nextFilter: Filter = filter) {
    setLoading(true);
    setError("");
    try {
      const suffix = nextFilter === "all" ? "" : `&status=${encodeURIComponent(nextFilter)}`;
      const result = await redpaFetch<ReviewList>(`/api/v1/reviews?limit=100&offset=0${suffix}`, {}, true);
      setReviews(result.items);
      setTotal(result.total);
      if (selected) {
        const refreshed = result.items.find((item) => item.id === selected.id);
        if (refreshed) setSelected(refreshed);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load human reviews");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [filter]);

  async function decide(action: "approve" | "reject") {
    if (!selected) return;
    setActing(action);
    setError("");
    setNotice("");
    try {
      const result = await redpaFetch<Review>(`/api/v1/reviews/${selected.id}/${action}`, {
        method: "POST",
        body: JSON.stringify({ feedback: feedback.trim() || null }),
      }, true);
      setSelected(result);
      setNotice(`Review ${action === "approve" ? "approved" : "rejected"}.`);
      setFeedback("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} review`);
    } finally {
      setActing("");
    }
  }

  async function resume() {
    if (!selected) return;
    setActing("resume");
    setError("");
    setNotice("");
    try {
      const result = await redpaFetch<Review>(`/api/v1/reviews/${selected.id}/resume`, { method: "POST", body: JSON.stringify({}) }, true);
      setSelected(result);
      setNotice("Approved workflow resumed successfully.");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow resume failed");
    } finally {
      setActing("");
    }
  }

  const counts = useMemo(() => ({
    pending: reviews.filter((item) => item.status.toLowerCase() === "pending").length,
    approved: reviews.filter((item) => item.status.toLowerCase() === "approved").length,
    rejected: reviews.filter((item) => item.status.toLowerCase() === "rejected").length,
  }), [reviews]);

  return <>
    <header className="cpHeader"><div><p className="cpEyebrow">CONTROL PLANE / HUMAN REVIEW</p><h1>Human Review Console</h1><p>Authenticated review queue for persisted Human-in-the-Loop decisions and workflow resume.</p></div><button onClick={() => void load()} disabled={loading}>{loading ? "Refreshing…" : "Refresh"}</button></header>
    {notice ? <div className="cpSuccess">{notice}</div> : null}
    {error ? <div className="cpNotice">{error}</div> : null}
    <section className="cpMetrics"><MetricCard label="Visible reviews" value={total} /><MetricCard label="Pending" value={counts.pending} /><MetricCard label="Approved" value={counts.approved} /><MetricCard label="Rejected" value={counts.rejected} /></section>

    <section className="cpPanel"><div className="cpPanelHead"><div><span>Queue</span><h2>Review requests</h2></div><div className="cpFilters">{(["all", "pending", "approved", "rejected"] as Filter[]).map((value) => <button key={value} className={filter === value ? "active" : ""} onClick={() => setFilter(value)}>{value}</button>)}</div></div>
      <div className="cpTableWrap"><table className="cpTable"><thead><tr><th>Request</th><th>Status</th><th>Action</th><th>Created</th><th></th></tr></thead><tbody>{reviews.map((review) => <tr key={review.id}><td><strong>{review.reason}</strong><small>{review.id}</small></td><td><StatusBadge value={review.status} /></td><td>{review.requested_action || "—"}</td><td>{new Date(review.created_at).toLocaleString()}</td><td><button className="cpLinkButton" onClick={() => { setSelected(review); setFeedback(""); }}>Inspect</button></td></tr>)}</tbody></table></div>
      {!reviews.length ? <p className="cpMuted">No reviews match the selected filter, or authentication is required.</p> : null}
    </section>

    {selected ? <section className="cpPanel"><div className="cpPanelHead"><div><span>Review detail</span><h2>{selected.requested_action || "Human approval request"}</h2></div><StatusBadge value={selected.status} /></div>
      <div className="cpDetailGrid"><div><span>Review ID</span><strong>{selected.id}</strong></div><div><span>Conversation</span><strong>{selected.conversation_id}</strong></div><div><span>Created</span><strong>{new Date(selected.created_at).toLocaleString()}</strong></div><div><span>Reviewed</span><strong>{selected.reviewed_at ? new Date(selected.reviewed_at).toLocaleString() : "Pending"}</strong></div></div>
      <div className="cpResponse"><span>Reason</span><p>{selected.reason}</p></div>
      {selected.request_content ? <div className="cpResponse"><span>Request content</span><p>{selected.request_content}</p></div> : null}
      {selected.action_payload ? <div className="cpResponse"><span>Action payload</span><pre>{JSON.stringify(selected.action_payload, null, 2)}</pre></div> : null}
      {selected.reviewer_feedback ? <div className="cpResponse"><span>Reviewer feedback</span><p>{selected.reviewer_feedback}</p></div> : null}
      {selected.status.toLowerCase() === "pending" ? <div className="cpDecision"><textarea value={feedback} onChange={(event) => setFeedback(event.target.value)} maxLength={5000} placeholder="Optional reviewer feedback" /><div className="cpActions"><button onClick={() => void decide("approve")} disabled={!!acting}>{acting === "approve" ? "Approving…" : "Approve"}</button><button className="cpDanger" onClick={() => void decide("reject")} disabled={!!acting}>{acting === "reject" ? "Rejecting…" : "Reject"}</button></div></div> : null}
      {selected.status.toLowerCase() === "approved" ? <div className="cpActions"><button onClick={() => void resume()} disabled={!!acting}>{acting === "resume" ? "Resuming…" : "Resume workflow"}</button></div> : null}
    </section> : null}
  </>;
}
