import { useState } from "react";
import { useNavigate } from "react-router-dom";

import AgentPanel from "@/components/AgentPanel";
import Header from "@/components/Header";
import NewsFeed from "@/components/NewsFeed";
import StatsBar from "@/components/StatsBar";
import TopicQueryBar from "@/components/TopicQueryBar";
import TrendingSidebar from "@/components/TrendingSidebar";
import {
  AnalysisJob,
  AnalysisReport,
  analyzeTopic,
  getAnalysisResult,
  getAuthSession,
  logoutUser,
} from "@/lib/api";

const POLL_INTERVAL_MS = 1500;
const POLL_TIMEOUT_MS = 120000;

const sleep = (durationMs: number) =>
  new Promise((resolve) => window.setTimeout(resolve, durationMs));

const pollJobUntilFinished = async (jobId: string): Promise<AnalysisJob> => {
  const startedAt = Date.now();

  while (Date.now() - startedAt < POLL_TIMEOUT_MS) {
    const job = await getAnalysisResult(jobId);
    if (job.status === "completed" || job.status === "failed") {
      return job;
    }

    await sleep(POLL_INTERVAL_MS);
  }

  throw new Error("Analysis timed out while waiting for the worker.");
};

const Index = () => {
  const navigate = useNavigate();
  const authSession = getAuthSession();
  const [topic, setTopic] = useState("AI regulation");
  const [format, setFormat] = useState("brief_summary");
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);
  const [lastJobId, setLastJobId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogout = () => {
    logoutUser();
    navigate("/auth", { replace: true });
  };

  const handleAnalyze = async ({ topic, format }: { topic: string; format: string }) => {
    setTopic(topic);
    setFormat(format);
    setError(null);
    setIsAnalyzing(true);
    setReport(null);
    setLastJobId(null);

    try {
      const queuedJob = await analyzeTopic({
        query: topic,
        report_format: format,
      });
      const finishedJob =
        queuedJob.status === "completed"
          ? queuedJob
          : await pollJobUntilFinished(queuedJob.job_id);

      if (finishedJob.status === "failed") {
        throw new Error(finishedJob.error || "Analysis failed.");
      }

      setReport(finishedJob.result ?? null);
      setLastUpdatedAt(finishedJob.updated_at);
      setLastJobId(finishedJob.job_id);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to generate report.";
      setError(message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header username={authSession?.username} onLogout={handleLogout} />
      <main className="container space-y-6 px-6 py-6">
        <TopicQueryBar onAnalyze={handleAnalyze} isLoading={isAnalyzing} />
        {error && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-2 text-xs text-destructive">
            {error}
          </div>
        )}
        <StatsBar report={report} isLoading={isAnalyzing} />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-7 xl:col-span-8">
            <NewsFeed
              topic={topic}
              report={report}
              format={format}
              analyzedAt={lastUpdatedAt}
              jobId={lastJobId}
              isReportLoading={isAnalyzing}
            />
          </div>
          <div className="space-y-6 lg:col-span-5 xl:col-span-4">
            <AgentPanel isAnalyzing={isAnalyzing} hasReport={Boolean(report)} />
            <TrendingSidebar report={report} isLoading={isAnalyzing} topic={topic} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
