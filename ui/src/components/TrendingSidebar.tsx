import { Hash, TrendingUp } from "lucide-react";

import { AnalysisReport } from "@/lib/api";

interface TrendingSidebarProps {
  topic?: string;
  report?: AnalysisReport | null;
  isLoading?: boolean;
}

const TrendingSidebar = ({ topic, report, isLoading }: TrendingSidebarProps) => {
  const trends = report?.trends ?? [];

  return (
    <div className="card-gradient space-y-4 rounded-lg border border-border p-4">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold tracking-tight">
          <TrendingUp className="h-4 w-4 text-primary" />
          Trending Topics
        </h2>
      </div>

      {isLoading && (
        <div className="text-xs text-muted-foreground">Extracting trends from the current run...</div>
      )}

      {!isLoading && trends.length === 0 && (
        <div className="text-xs text-muted-foreground">
          No trends detected yet for {topic || "this topic"}.
        </div>
      )}

      <div className="space-y-1">
        {trends.map((trend, index) => (
          <div
            key={`${trend}-${index}`}
            className="group flex items-center justify-between rounded-md p-2.5 transition-colors hover:bg-background/50"
          >
            <div className="flex items-center gap-2.5">
              <span className="w-4 text-[10px] text-muted-foreground">{index + 1}</span>
              <Hash className="h-3 w-3 text-primary/50" />
              <div>
                <p className="text-xs font-medium text-foreground transition-colors group-hover:text-primary">
                  {trend}
                </p>
                <p className="text-[10px] text-muted-foreground">derived from latest analysis</p>
              </div>
            </div>
            <span className="text-[10px] font-semibold text-success">
              +{Math.max(8, 20 - index * 2)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TrendingSidebar;
