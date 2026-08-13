export default function StatusBadge({ value }: { value?: string }) {
  const normalized = (value || "unknown").toLowerCase();
  const tone = ["healthy", "ready", "active", "available", "closed"].includes(normalized)
    ? "ok"
    : ["degraded", "pending", "half_open"].includes(normalized)
      ? "warn"
      : ["offline", "unhealthy", "unavailable", "open", "failed"].includes(normalized)
        ? "bad"
        : "neutral";
  return <span className={`cpStatus ${tone}`}>{value || "unknown"}</span>;
}
