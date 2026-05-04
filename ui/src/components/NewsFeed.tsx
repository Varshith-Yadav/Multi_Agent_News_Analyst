import { useState } from "react";
import { AlertTriangle, CheckCircle2, Clock, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AnalysisReport, followUpReport } from "@/lib/api";
import { formatRelativeTime } from "@/lib/time";

interface NewsFeedProps {
  topic?: string;
  report?: AnalysisReport | null;
  format?: string;
  analyzedAt?: string | null;
  jobId?: string | null;
  isReportLoading?: boolean;
}

const formatPercent = (value?: number | null) =>
  typeof value === "number" ? `${Math.round(value * 100)}%` : "—";

const NewsFeed = ({
  topic,
  report,
  format,
  analyzedAt,
  jobId,
  isReportLoading,
}: NewsFeedProps) => {
  const verificationItems = report?.verified_claims ?? [];
  const sourceItems = report?.source_attribution ?? [];
  const [followupQuestion, setFollowupQuestion] = useState("");
  const [followupMode, setFollowupMode] = useState<
    "follow_up" | "refine_topic" | "opposing_viewpoints"
  >("follow_up");
  const [followupAnswer, setFollowupAnswer] = useState<string | null>(null);
  const [isFollowupLoading, setIsFollowupLoading] = useState(false);

  const handleFollowup = async () => {
    if (!jobId || !followupQuestion.trim()) {
      return;
    }

    try {
      setIsFollowupLoading(true);
      const response = await followUpReport({
        job_id: jobId,
        question: followupQuestion.trim(),
        mode: followupMode,
      });
      setFollowupAnswer(response.answer);
    } catch (error) {
      setFollowupAnswer(
        error instanceof Error ? error.message : "Unable to run follow-up query."
      );
    } finally {
      setIsFollowupLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-tight">Analysis Output</h2>
        <span className="text-[10px] text-muted-foreground">
          Last updated: {formatRelativeTime(analyzedAt)}
        </span>
      </div>

      {report && (
        <article className="glow-border card-gradient space-y-3 rounded-lg border border-primary/30 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="border-primary/40 bg-primary/10 text-[10px] text-primary">
              Latest Report
            </Badge>
            <Badge variant="outline" className="text-[10px]">
              {topic || "Topic"}
            </Badge>
            <Badge variant="outline" className="text-[10px]">
              {format ? format.replace(/_/g, " ") : "analysis"}
            </Badge>
          </div>

          <div className="space-y-2">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <Sparkles className="h-4 w-4 text-primary" />
              Executive Summary
            </h3>
            <p className="whitespace-pre-line break-words text-xs leading-relaxed text-muted-foreground">
              {report.summary || "No summary available."}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-[11px] text-muted-foreground">
            <span>
              Sentiment: <span className="font-semibold text-foreground">{report.sentiment || "—"}</span>
            </span>
            <span>
              Credibility: <span className="font-semibold text-foreground">{formatPercent(report.credibility)}</span>
            </span>
            <span>
              Confidence: <span className="font-semibold text-foreground">{formatPercent(report.confidence)}</span>
            </span>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-foreground">Top Sources</h4>
            {sourceItems.length === 0 && (
              <p className="text-xs text-muted-foreground">No source links available for this run.</p>
            )}
            {sourceItems.slice(0, 5).map((source, index) => (
              <div
                key={`${source.url ?? source.title ?? "source"}-${index}`}
                className="min-w-0 text-xs"
              >
                <a
                  href={source.url || "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="line-clamp-2 break-all text-primary hover:underline"
                >
                  {source.title || source.source || "Untitled source"}
                </a>
                <span className="ml-2 break-words text-muted-foreground">
                  ({source.source || "unknown"})
                </span>
              </div>
            ))}
          </div>
        </article>
      )}

      {isReportLoading && (
        <div className="card-gradient rounded-lg border border-border p-4 text-xs text-muted-foreground">
          Running multi-agent analysis...
        </div>
      )}

      {!report && !isReportLoading && (
        <div className="card-gradient rounded-lg border border-border p-4 text-xs text-muted-foreground">
          Submit a topic to generate a summary, sentiment signal, credibility score, trends, and verification notes.
        </div>
      )}

      {report && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">Verification Notes</h3>
            <span className="text-[10px] text-muted-foreground">
              {verificationItems.length} items
            </span>
          </div>

          {verificationItems.length === 0 && (
            <div className="card-gradient rounded-lg border border-border p-4 text-xs text-muted-foreground">
              No verification details were returned for this run.
            </div>
          )}

          {verificationItems.map((item, index) => (
            <article
              key={`${item.claim_id ?? "verification"}-${index}`}
              className="card-gradient rounded-lg border border-border p-4 transition-all hover:border-primary/30"
            >
              <div className="mb-2 flex items-center gap-2">
                {index % 2 === 0 ? (
                  <CheckCircle2 className="h-4 w-4 text-success" />
                ) : (
                  <Clock className="h-4 w-4 text-warning" />
                )}
                <span className="text-xs font-semibold text-foreground">
                  Verification #{index + 1}
                </span>
              </div>
              <p className="break-words text-xs leading-relaxed text-muted-foreground">
                {item.claim || "Claim details unavailable."}
              </p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                Status:{" "}
                <span className="font-semibold text-foreground">
                  {item.verification_status || "unknown"}
                </span>
                {" · "}
                Sources:{" "}
                <span className="font-semibold text-foreground">
                  {item.supporting_source_count ?? 0}/{item.required_sources ?? 3}
                </span>
              </p>
            </article>
          ))}
        </div>
      )}

      {report?.summary && !report.verified_claims?.length && (
        <div className="rounded-lg border border-warning/30 bg-warning/10 p-3 text-xs text-warning">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Verification details are limited because the current pipeline returned summary-focused output.
          </div>
        </div>
      )}

      {report && jobId && (
        <div className="card-gradient space-y-3 rounded-lg border border-border p-4">
          <h3 className="text-sm font-semibold text-foreground">Follow-up Intelligence</h3>
          <div className="flex flex-col gap-2 lg:flex-row">
            <Input
              value={followupQuestion}
              onChange={(event) => setFollowupQuestion(event.target.value)}
              placeholder="Ask follow-up, refine topic, or request opposing viewpoints"
              className="flex-1"
            />
            <Select
              value={followupMode}
              onValueChange={(value) =>
                setFollowupMode(value as "follow_up" | "refine_topic" | "opposing_viewpoints")
              }
            >
              <SelectTrigger className="w-full lg:w-52">
                <SelectValue placeholder="Mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="follow_up">Follow-up</SelectItem>
                <SelectItem value="refine_topic">Refine Topic</SelectItem>
                <SelectItem value="opposing_viewpoints">Opposing Views</SelectItem>
              </SelectContent>
            </Select>
            <Button
              onClick={handleFollowup}
              disabled={isFollowupLoading || !followupQuestion.trim()}
              className="w-full lg:w-auto"
            >
              {isFollowupLoading ? "Processing..." : "Ask"}
            </Button>
          </div>
          {followupAnswer && (
            <p className="rounded-md border border-border/60 bg-background/40 p-3 text-xs leading-relaxed text-muted-foreground">
              {followupAnswer}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default NewsFeed;
