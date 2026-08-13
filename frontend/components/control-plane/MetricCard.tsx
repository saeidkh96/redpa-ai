export default function MetricCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <article className="cpMetric"><span>{label}</span><strong>{value}</strong>{hint ? <small>{hint}</small> : null}</article>;
}
