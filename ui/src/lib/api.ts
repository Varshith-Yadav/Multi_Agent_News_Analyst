const CORE_API_BASE =
  import.meta.env.VITE_CORE_API_BASE_URL ?? "http://localhost:8000";

const SESSION_STORAGE_KEY = "mana.auth.session";

export interface AuthSession {
  username: string;
  accessToken: string;
  tokenType: string;
  expiresAtEpoch: number;
  roles: string[];
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  roles: string[];
}

export interface AnalysisReport {
  report_format?: string | null;
  summary?: string | null;
  quick_brief?: string[] | null;
  sentiment?: string | null;
  trends?: string[] | null;
  trend_analysis?: Array<{
    keyword: string;
    spike_score: number;
    mentions: number;
    evolution: string;
  }> | null;
  credibility?: number | null;
  source_attribution?: Array<{
    source?: string;
    title?: string;
    url?: string;
    published_at?: string;
    credibility_score?: number;
    verification_status?: string;
  }> | null;
  verified_claims?: Array<{
    claim_id?: string;
    claim?: string;
    verification_status?: string;
    supporting_source_count?: number;
    required_sources?: number;
    confidence?: number;
  }> | null;
  confidence?: number | null;
  alerts?: Array<{
    type: string;
    message: string;
    confidence?: number;
  }> | null;
  daily_digest?: string[] | null;
  weekly_trend_report?: Record<string, unknown> | null;
  deep_dive?: Record<string, unknown> | null;
  industry_snapshot?: Record<string, unknown> | null;
}

export interface AnalysisJob {
  job_id: string;
  query: string;
  report_format: string;
  region?: string | null;
  industry?: string | null;
  time_window_hours: number;
  status: "queued" | "running" | "completed" | "failed";
  result?: AnalysisReport | null;
  error?: string | null;
  cached: boolean;
  created_at: string;
  updated_at: string;
}

export interface FollowupResponse {
  job_id: string;
  mode: "follow_up" | "refine_topic" | "opposing_viewpoints";
  answer: string;
  refined_query?: string | null;
  suggested_next_questions?: string[];
}

function readSessionFromStorage(): AuthSession | null {
  try {
    const raw = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as AuthSession;
    if (!parsed.accessToken || !parsed.username || !parsed.expiresAtEpoch) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function persistSession(session: AuthSession | null): void {
  if (!session) {
    window.localStorage.removeItem(SESSION_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

let authSession: AuthSession | null = readSessionFromStorage();

function nowEpoch(): number {
  return Math.floor(Date.now() / 1000);
}

function setSession(username: string, token: TokenResponse): AuthSession {
  const session: AuthSession = {
    username,
    accessToken: token.access_token,
    tokenType: token.token_type,
    expiresAtEpoch: nowEpoch() + token.expires_in,
    roles: token.roles ?? [],
  };
  authSession = session;
  persistSession(session);
  return session;
}

export function getAuthSession(): AuthSession | null {
  return authSession;
}

export function isAuthenticated(): boolean {
  return Boolean(authSession && authSession.expiresAtEpoch > nowEpoch() + 30);
}

export function logoutUser(): void {
  authSession = null;
  persistSession(null);
}

export async function loginUser(payload: {
  username: string;
  password: string;
}): Promise<AuthSession> {
  const form = new URLSearchParams();
  form.append("username", payload.username);
  form.append("password", payload.password);

  const response = await fetch(`${CORE_API_BASE}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Login failed.");
  }

  const token = (await response.json()) as TokenResponse;
  return setSession(payload.username.trim().toLowerCase(), token);
}

export async function signupUser(payload: {
  username: string;
  password: string;
}): Promise<AuthSession> {
  const response = await fetch(`${CORE_API_BASE}/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Signup failed.");
  }

  const token = (await response.json()) as TokenResponse;
  return setSession(payload.username.trim().toLowerCase(), token);
}

async function ensureToken(): Promise<string> {
  if (!isAuthenticated() || !authSession) {
    throw new Error("Authentication required. Please sign in.");
  }
  return authSession.accessToken;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await ensureToken();
  const url = `${CORE_API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    headers: {
      ...(options.body instanceof URLSearchParams
        ? {}
        : { "Content-Type": "application/json" }),
      Authorization: `Bearer ${token}`,
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

export function analyzeTopic(payload: {
  query: string;
  report_format: string;
  region?: string;
  industry?: string;
  time_window_hours?: number;
}): Promise<AnalysisJob> {
  return request<AnalysisJob>("/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getAnalysisResult(jobId: string): Promise<AnalysisJob> {
  return request<AnalysisJob>(`/result/${jobId}`);
}

export function followUpReport(payload: {
  job_id: string;
  question: string;
  mode?: "follow_up" | "refine_topic" | "opposing_viewpoints";
}): Promise<FollowupResponse> {
  return request<FollowupResponse>("/follow-up", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
