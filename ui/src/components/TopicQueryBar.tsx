import { useState } from "react";
import { Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface TopicQueryBarProps {
  onAnalyze: (payload: { topic: string; format: string }) => void;
  isLoading?: boolean;
}

const formats = [
  { value: "brief_summary", label: "Brief Summary" },
  { value: "executive_summary", label: "Executive Summary" },
  { value: "deep_analytical_report", label: "Deep Analytical Report" },
  { value: "daily_digest", label: "Daily Digest" },
  { value: "weekly_trend_report", label: "Weekly Trend Report" },
  { value: "real_time_alert", label: "Real-Time Alerts" },
  { value: "industry_snapshot", label: "Industry Snapshot" },
];

const TopicQueryBar = ({ onAnalyze, isLoading }: TopicQueryBarProps) => {
  const [topic, setTopic] = useState("AI regulation");
  const [format, setFormat] = useState(formats[0].value);

  return (
    <div className="rounded-lg border border-border card-gradient p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3 text-sm font-semibold">
          <div className="w-9 h-9 rounded-md bg-primary/15 border border-primary/30 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight">Topic Intelligence</p>
            <p className="text-[11px] font-mono text-muted-foreground">
              Query the multi-agent graph for summaries, sentiment, and verification.
            </p>
          </div>
        </div>
        <div className="flex flex-1 flex-col gap-2 lg:flex-row lg:items-center lg:justify-end">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <Input
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Search a topic (e.g., AI regulation)"
              className="pl-9"
            />
          </div>
          <Select value={format} onValueChange={setFormat}>
            <SelectTrigger className="w-full lg:w-56">
              <SelectValue placeholder="Report format" />
            </SelectTrigger>
            <SelectContent>
              {formats.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            className="w-full lg:w-auto"
            onClick={() => topic.trim() && onAnalyze({ topic: topic.trim(), format })}
            disabled={isLoading || !topic.trim()}
          >
            {isLoading ? "Analyzing..." : "Analyze"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TopicQueryBar;
