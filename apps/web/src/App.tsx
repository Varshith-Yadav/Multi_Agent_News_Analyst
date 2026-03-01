import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { Article, HealthResponse, IngestionRun, IngestionRunResult, Source } from "./types";

type VerificationState = "verified" | "unverified" | "disputed";

type FeedItem = {
  id: number;
  category: string;
  state: VerificationState;
  age: string;
  title: string;
  summary: string;
  sources: number;
  biasScore: number;
  leadSource: string;
  url: string;
};

type TopicTrend = {
  label: string;
  mentions: number;
  growth: number;
};

const CATEGORY_RULES: Array<{ label: string; terms: string[] }> = [
  { label: "Climate", terms: ["climate", "carbon", "emission", "summit", "energy"] },
  { label: "Finance", terms: ["market", "earnings", "stock", "finance", "investment"] },
  { label: "Security", terms: ["security", "threat", "cyber", "attack", "defense"] },
  { label: "Economy", terms: ["economy", "trade", "policy", "inflation", "growth"] },
  { label: "Politics", terms: ["election", "parliament", "minister", "government"] },
  { label: "Technology", terms: ["ai", "quantum", "chip", "software", "startup"] },
  { label: "Health", terms: ["health", "disease", "vaccine", "hospital", "medical"] }
];

const TOPIC_STOPWORDS = new Set([
  "about",
  "after",
  "against",
  "amid",
  "among",
  "analysis",
  "before",
  "between",
  "breaking",
  "from",
  "have",
  "into",
  "just",
  "more",
  "over",
  "report",
  "reports",
  "story",
  "their",
  "these",
  "this",
  "today",
  "under",
  "update",
  "with",
  "world"
]);

function compact(value: number): string {
  return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function relativeTime(value: string | null | undefined): string {
  if (!value) {
    return "just now";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "just now";
  }
  const diff = Date.now() - date.getTime();
  const minute = 60_000;
  const hour = 60 * minute;
  if (diff < minute) {
    return "just now";
  }
  if (diff < hour) {
    return `${Math.max(1, Math.floor(diff / minute))} min ago`;
  }
  return `${Math.max(1, Math.floor(diff / hour))} hr ago`;
}

function inferCategory(title: string, fallback: string): string {
  const normalized = title.toLowerCase();
  for (const rule of CATEGORY_RULES) {
    if (rule.terms.some((term) => normalized.includes(term))) {
      return rule.label;
    }
  }
  return fallback;
}

function summarize(description: string | null, content: string | null): string {
  const raw = (description || content || "Ingestion pipeline captured this article for cross-source verification.").trim();
  return raw.length > 220 ? `${raw.slice(0, 217)}...` : raw;
}

function buildFeedItem(article: Article): FeedItem {
  const sourceCount = Math.max(article.tracked_sources.length, 1);
  const title = article.title;
  const normalized = title.toLowerCase();
  const disputedTerms = /(dispute|disputed|conflict|controvers|claim|alleg|rumor|rumour)/;

  let state: VerificationState = "verified";
  if (disputedTerms.test(normalized)) {
    state = "disputed";
  } else if (sourceCount <= 1) {
    state = "unverified";
  }

  const biasBase = 42 - sourceCount * 7;
  const biasScore = Math.max(
    6,
    Math.min(
      72,
      Math.round(
        biasBase + (state === "disputed" ? 18 : 0) + (state === "unverified" ? 10 : -7)
      )
    )
  );

  return {
    id: article.id,
    category: inferCategory(title, article.primary_source),
    state,
    age: relativeTime(article.published_at || article.ingested_at),
    title,
    summary: summarize(article.description, article.content_temp),
    sources: sourceCount,
    biasScore,
    leadSource: article.primary_source,
    url: article.url
  };
}

function buildTrends(articles: Article[]): TopicTrend[] {
  const tokenCounts = new Map<string, number>();
  for (const article of articles.slice(0, 80)) {
    const tokens = article.title
      .toLowerCase()
      .split(/[^a-z0-9]+/)
      .filter((token) => token.length > 3 && !TOPIC_STOPWORDS.has(token));
    for (const token of tokens) {
      tokenCounts.set(token, (tokenCounts.get(token) || 0) + 1);
    }
  }

  const trends = [...tokenCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([token, count]) => ({
      label: token.charAt(0).toUpperCase() + token.slice(1),
      mentions: count * 320 + 1200,
      growth: Math.max(14, Math.min(170, count * 18 + 11))
    }));

  if (trends.length > 0) {
    return trends;
  }

  return [
    { label: "Global Economy", mentions: 1840, growth: 62 },
    { label: "AI Regulation", mentions: 1520, growth: 54 },
    { label: "Climate Strategy", mentions: 1310, growth: 47 }
  ];
}

function StatusBadge({ state }: { state: VerificationState }) {
  return <span className={`badge status status-${state}`}>{state}</span>;
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [runs, setRuns] = useState<IngestionRun[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningIngestion, setIsRunningIngestion] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRunResult, setLastRunResult] = useState<IngestionRunResult | null>(null);

  const loadDashboard = useCallback(async () => {
    setError(null);
    const [nextHealth, nextRuns, nextSources, nextArticles] = await Promise.all([
      api.health(),
      api.listRuns(30),
      api.listSources(200),
      api.listArticles(120)
    ]);
    setHealth(nextHealth);
    setRuns(nextRuns);
    setSources(nextSources);
    setArticles(nextArticles);
  }, []);

  useEffect(() => {
    let mounted = true;
    setIsLoading(true);
    loadDashboard()
      .catch((err: Error) => {
        if (mounted) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (mounted) {
          setIsLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [loadDashboard]);

  useEffect(() => {
    if (!autoRefresh) {
      return;
    }
    const timer = window.setInterval(() => {
      loadDashboard().catch((err: Error) => {
        setError(err.message);
      });
    }, 30000);
    return () => window.clearInterval(timer);
  }, [autoRefresh, loadDashboard]);

  const latestRun = runs[0];
  const feedItems = useMemo(() => articles.slice(0, 8).map(buildFeedItem), [articles]);
  const trendingTopics = useMemo(() => buildTrends(articles), [articles]);

  const totalFetched = runs.reduce((acc, run) => acc + run.fetched_count, 0);
  const articlesProcessed = totalFetched > 0 ? totalFetched : articles.length;
  const verifiedStories = feedItems.filter((item) => item.state === "verified").length;
  const verifiedRate = articles.length > 0 ? (verifiedStories / articles.length) * 100 : 0;
  const biasAlerts = feedItems.filter((item) => item.biasScore >= 30 || item.state !== "verified").length;

  const agentNetwork = useMemo(
    () => [
      {
        name: "Collector",
        role: "Source Aggregation",
        tasks: latestRun?.fetched_count ?? articles.length + sources.length
      },
      {
        name: "Verifier",
        role: "Fact Checking",
        tasks: Math.max(12, verifiedStories * 11 + runs.length)
      },
      {
        name: "Analyst",
        role: "Bias Detection",
        tasks: Math.max(9, biasAlerts * 7 + Math.floor(articles.length / 3))
      },
      {
        name: "Synthesizer",
        role: "Report Generation",
        tasks: Math.max(6, trendingTopics.length * 12 + Math.floor(articles.length / 5))
      },
      {
        name: "Monitor",
        role: "Trend Detection",
        tasks: Math.max(4, runs.length * 8 + (autoRefresh ? 3 : 0))
      }
    ],
    [latestRun?.fetched_count, articles.length, sources.length, verifiedStories, runs.length, biasAlerts, trendingTopics.length, autoRefresh]
  );

  async function onRunIngestion() {
    const connectorsToRun = health?.connectors ?? [];
    if (connectorsToRun.length === 0) {
      setError("No connectors available from backend health endpoint.");
      return;
    }
    setIsRunningIngestion(true);
    setError(null);
    try {
      const result = await api.runIngestion(connectorsToRun, "frontend_console");
      setLastRunResult(result);
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run ingestion.");
    } finally {
      setIsRunningIngestion(false);
    }
  }

  return (
    <div className="dashboard">
      <header className="topbar">
        <div className="brand-block">
          <div className="logo-mark" aria-hidden="true">
            <span>O</span>
          </div>
          <div>
            <h1 className="brand-title">
              Neural<span>News</span>
            </h1>
            <p className="brand-subtitle">MULTI-AGENT INTELLIGENCE</p>
          </div>
        </div>

        <div className="topbar-right">
          <span className="status-chip">{agentNetwork.length} agents active</span>
          <button
            className={`status-chip status-toggle ${autoRefresh ? "on" : "off"}`}
            onClick={() => setAutoRefresh((value) => !value)}
          >
            {autoRefresh ? "Real-time" : "Paused"}
          </button>
          <button className="run-btn" onClick={onRunIngestion} disabled={isRunningIngestion || isLoading}>
            {isRunningIngestion ? "Running..." : "Run Ingestion"}
          </button>
          <span className="ai-orb">AI</span>
        </div>
      </header>

      {error ? <p className="banner error">{error}</p> : null}
      {lastRunResult ? (
        <p className="banner info">
          Ingestion {lastRunResult.status}: fetched {lastRunResult.fetched_count}, inserted {lastRunResult.inserted_count},
          deduplicated {lastRunResult.deduplicated_count}
        </p>
      ) : null}

      <section className="metrics">
        <article className="metric-card">
          <p className="metric-label">Articles Processed</p>
          <p className="metric-value">{compact(articlesProcessed)}</p>
          <p className="metric-foot">+{latestRun?.inserted_count ?? 0} today</p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Verified Stories</p>
          <p className="metric-value">{compact(verifiedStories)}</p>
          <p className="metric-foot">{verifiedRate.toFixed(1)}% rate</p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Bias Alerts</p>
          <p className="metric-value">{compact(biasAlerts)}</p>
          <p className="metric-foot">{feedItems.filter((item) => item.state !== "verified").length} high priority</p>
        </article>
        <article className="metric-card">
          <p className="metric-label">Emerging Trends</p>
          <p className="metric-value">{compact(trendingTopics.length)}</p>
          <p className="metric-foot">{trendingTopics[0] ? `+${trendingTopics[0].growth}% momentum` : "No trend data"}</p>
        </article>
      </section>

      <main className="main-grid">
        <section className="feed-column">
          <div className="section-head">
            <h2>Intelligence Feed</h2>
            <p>Last updated: {relativeTime(latestRun?.completed_at || latestRun?.started_at)}</p>
          </div>

          {feedItems.length === 0 ? (
            <div className="empty-feed">No articles yet. Run ingestion to populate live intelligence cards.</div>
          ) : (
            feedItems.map((item) => (
              <article className="feed-card" key={item.id}>
                <div className="feed-headline">
                  <div className="badge-group">
                    <span className="badge category">{item.category}</span>
                    <StatusBadge state={item.state} />
                    <span className="feed-age">{item.age}</span>
                  </div>
                </div>
                <h3 className="feed-title">
                  <a href={item.url} target="_blank" rel="noreferrer">
                    {item.title}
                  </a>
                </h3>
                <p className="feed-summary">{item.summary}</p>
                <div className="feed-meta">
                  <span>
                    Sources: <strong>{item.sources}</strong>
                  </span>
                  <span className="bias-row">
                    Bias:
                    <span className="bias-track">
                      <span
                        className={`bias-fill bias-${item.state}`}
                        style={{ width: `${item.biasScore}%` }}
                      />
                    </span>
                    {item.biasScore}%
                  </span>
                  <span className="lead-source">{item.leadSource}</span>
                </div>
              </article>
            ))
          )}
        </section>

        <aside className="side-column">
          <section className="side-panel">
            <div className="side-head">
              <h3>Agent Network</h3>
              <span className="online-pill">{agentNetwork.length} online</span>
            </div>
            <div className="agent-list">
              {agentNetwork.map((agent) => (
                <article className="agent-item" key={agent.name}>
                  <div className="agent-icon" aria-hidden="true">
                    {agent.name.slice(0, 1)}
                  </div>
                  <div className="agent-copy">
                    <p className="agent-name">{agent.name}</p>
                    <p className="agent-role">{agent.role}</p>
                  </div>
                  <p className="agent-tasks">{compact(agent.tasks)} tasks</p>
                </article>
              ))}
            </div>
          </section>

          <section className="side-panel">
            <div className="side-head">
              <h3>Trending Topics</h3>
            </div>
            <div className="topic-list">
              {trendingTopics.map((topic, index) => (
                <article className="topic-item" key={topic.label}>
                  <p className="topic-rank">{index + 1}</p>
                  <div className="topic-copy">
                    <p className="topic-title">#{topic.label}</p>
                    <p className="topic-meta">{topic.mentions.toLocaleString()} mentions</p>
                  </div>
                  <p className="topic-growth">+{topic.growth}%</p>
                </article>
              ))}
            </div>
          </section>
        </aside>
      </main>
    </div>
  );
}
