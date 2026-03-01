import type {
  Article,
  HealthResponse,
  IngestionRun,
  IngestionRunResult,
  Source
} from "./types";

const baseUrl =
  (import.meta.env.VITE_INGESTION_API_BASE_URL as string | undefined)?.trim() ||
  "http://localhost:8010";

const apiBase = `${baseUrl.replace(/\/+$/, "")}/v1`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export const api = {
  baseUrl: apiBase,
  health: () => request<HealthResponse>("/health"),
  listRuns: (limit = 20) => request<IngestionRun[]>(`/ingestion/runs?limit=${limit}`),
  listSources: (limit = 100) => request<Source[]>(`/sources?limit=${limit}`),
  listArticles: (limit = 100) => request<Article[]>(`/articles?limit=${limit}`),
  runIngestion: (connectors: string[], triggeredBy: string) =>
    request<IngestionRunResult>("/ingestion/run", {
      method: "POST",
      body: JSON.stringify({
        connectors,
        triggered_by: triggeredBy
      })
    })
};
