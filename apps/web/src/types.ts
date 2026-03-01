export type HealthResponse = {
  status: string;
  service: string;
  environment: string;
  connectors: string[];
};

export type IngestionRun = {
  id: number;
  triggered_by: string;
  connectors: string[];
  status: string;
  started_at: string;
  completed_at: string | null;
  fetched_count: number;
  inserted_count: number;
  deduplicated_count: number;
  errors_count: number;
  error_message: string | null;
};

export type IngestionRunResult = {
  run_id: number | null;
  status: string;
  connectors: string[];
  fetched_count: number;
  inserted_count: number;
  deduplicated_count: number;
  errors_count: number;
  error_message: string | null;
};

export type Source = {
  id: number;
  source_type: string;
  name: string;
  url: string;
  external_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Article = {
  id: number;
  title: string;
  url: string;
  canonical_url: string;
  description: string | null;
  content_temp: string | null;
  author: string | null;
  language: string | null;
  region: string | null;
  published_at: string | null;
  ingested_at: string;
  first_seen_at: string;
  last_seen_at: string;
  content_hash: string;
  primary_source: string;
  tracked_sources: string[];
};
