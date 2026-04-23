import { AlertTriangle, Gauge, ShieldCheck, TrendingUp } from "lucide-react";

import { AnalysisReport } from "@/lib/api";

interface StatsBarProps {
  report?: AnalysisReport | null;
  isLoading?: boolean;
}

const formatPercent = (value?: number | null) =>
  typeof value === "number" ? `${Math.round(value * 100)}%` : "—";

const titleCase = (value?: string | null) =>
  value ? `${value.charAt(0).toUpperCase()}${value.slice(1)}` : "—";

const StatsBar = ({ report, isLoading }: StatsBarProps) => {
  const verifiedClaims = report?.verified_claims?.length ?? 0;
  const trendsCount = report?.trends?.length ?? 0;

  const stats = [
    {
      label: "Sentiment",
      value: titleCase(report?.sentiment),
      sub: report ? "latest report signal" : isLoading ? "running analysis" : "waiting for topic",
      icon: <AlertTriangle className="h-4 w-4" />,
    },
    {
      label: "Confidence",
      value: formatPercent(report?.confidence),
      sub: report ? "final graph score" : isLoading ? "calculating score" : "no result yet",
      icon: <Gauge className="h-4 w-4" />,
    },
    {
      label: "Credibility",
      value: formatPercent(report?.credibility),
      sub: report ? "source trust estimate" : isLoading ? "evaluating sources" : "not evaluated",
      icon: <ShieldCheck className="h-4 w-4" />,
    },
    {
      label: "Signals",
      value: verifiedClaims ? verifiedClaims.toString() : "—",
      sub: report ? `${trendsCount} trends extracted` : isLoading ? "extracting patterns" : "no signals yet",
      icon: <TrendingUp className="h-4 w-4" />,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="card-gradient rounded-lg border border-border p-4 transition-colors hover:border-primary/30"
        >
          <div className="mb-2 flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
              {stat.label}
            </span>
            <div className="text-primary/60">{stat.icon}</div>
          </div>
          <p className="text-2xl font-bold tracking-tight text-foreground">{stat.value}</p>
          <p className="mt-1 text-[11px] text-primary">{stat.sub}</p>
        </div>
      ))}
    </div>
  );
};

export default StatsBar;
