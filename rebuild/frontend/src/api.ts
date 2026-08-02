/** Thin API client for auth + resumes (Phase 1–2). */

import { authHeaders, clearToken, setToken } from "./session";

const API = "/api/v1";

export type TokenResponse = {
  access_token: string;
  token_type: string;
  email: string;
  user_id: string;
};

export type ResumeListItem = {
  id: string;
  title: string;
  track: string;
  tags: string[];
};

export type ResumeDetail = ResumeListItem & {
  form?: Record<string, unknown> | null;
  latex_source?: string | null;
  mode?: string;
  show_form_tab?: boolean;
  show_source_editor?: boolean;
  show_lint?: boolean;
};

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail
        .map((d: { msg?: string }) => d.msg || String(d))
        .join("; ");
    }
    return res.statusText || `HTTP ${res.status}`;
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

async function authed(res: Response): Promise<Response> {
  if (res.status === 401 || res.status === 403) {
    clearToken();
    throw new Error("unauthorized");
  }
  return res;
}

export async function register(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const res = await fetch(`${API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  const body = (await res.json()) as TokenResponse;
  setToken(body.access_token);
  return body;
}

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  const body = (await res.json()) as TokenResponse;
  setToken(body.access_token);
  return body;
}

export async function logout(): Promise<void> {
  try {
    await fetch(`${API}/auth/logout`, {
      method: "POST",
      headers: { ...authHeaders() },
    });
  } finally {
    clearToken();
  }
}

export async function listResumes(opts?: {
  q?: string;
  tags?: string[];
}): Promise<ResumeListItem[]> {
  const params = new URLSearchParams();
  if (opts?.q) params.set("q", opts.q);
  if (opts?.tags?.length) params.set("tags", opts.tags.join(","));
  const qs = params.toString();
  const res = await authed(
    await fetch(`${API}/resumes${qs ? `?${qs}` : ""}`, {
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ResumeListItem[];
}

export async function createResume(
  kind: "ai" | "latex",
): Promise<ResumeDetail> {
  const res = await authed(
    await fetch(`${API}/resumes`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({ create: kind }),
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ResumeDetail;
}

export async function getResume(id: string): Promise<ResumeDetail> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}`, {
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ResumeDetail;
}

export async function deleteResume(id: string): Promise<void> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}`, {
      method: "DELETE",
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok && res.status !== 204) throw new Error(await parseError(res));
}

export async function patchResume(
  id: string,
  body: {
    title?: string;
    tags?: string[];
    form?: Record<string, unknown>;
    latex_source?: string;
  },
): Promise<ResumeDetail> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify(body),
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ResumeDetail;
}

export type CompileResult = {
  ok: boolean;
  engine: string;
  size: number;
};

export type Diagnostic = {
  severity: string;
  message: string;
  line?: number;
  suggestion?: string;
};

export async function compileResume(id: string): Promise<CompileResult> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}/compile`, {
      method: "POST",
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as CompileResult;
}

export async function lintResume(
  id: string,
): Promise<{ diagnostics: Diagnostic[]; count: number }> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}/lint`, {
      method: "POST",
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as { diagnostics: Diagnostic[]; count: number };
}

/** Fetch PDF as Blob for iframe preview (native browser PDF, not pdf.js). */
export async function fetchPdfBlob(id: string): Promise<Blob> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}/pdf`, {
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return res.blob();
}

export async function downloadFile(
  id: string,
  kind: "pdf" | "tex",
): Promise<void> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}/${kind}`, {
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  const blob = await res.blob();
  const cd = res.headers.get("content-disposition") || "";
  const m = /filename="?([^";]+)"?/.exec(cd);
  const name = m?.[1] || `resume.${kind}`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

/** Phase 6 — LaTeX version checkpoints */
export type Checkpoint = {
  id: string;
  resume_id?: string;
  message: string;
  created_at: string;
  latex_source?: string;
};

export type CommitVersionResult = {
  committed: boolean;
  unchanged?: boolean;
  message?: string;
  checkpoint?: Checkpoint;
};

export async function listVersions(id: string): Promise<Checkpoint[]> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}/versions`, {
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as Checkpoint[];
}

export async function commitVersion(
  id: string,
  message?: string,
): Promise<CommitVersionResult> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}/versions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({ message: message || undefined }),
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as CommitVersionResult;
}

export async function restoreVersion(
  id: string,
  checkpointId: string,
): Promise<ResumeDetail & { restored?: boolean; message?: string; compile_engine?: string }> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}/versions/${checkpointId}/restore`, {
      method: "POST",
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ResumeDetail & {
    restored?: boolean;
    message?: string;
    compile_engine?: string;
  };
}

export async function deleteVersion(
  id: string,
  checkpointId: string,
): Promise<void> {
  const res = await authed(
    await fetch(`${API}/resumes/${id}/versions/${checkpointId}`, {
      method: "DELETE",
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok && res.status !== 204) throw new Error(await parseError(res));
}

/** Phase 7 — settings + score */
export type UserSettings = {
  email?: string;
  github_username: string;
  github_cache?: {
    login?: string;
    username?: string;
    repo_count?: number;
    repos?: unknown[];
    fetched_at?: string;
  } | null;
  cache_updated_at?: string | null;
  cache_status: string;
  ok?: boolean;
};

export type ScoreCategory = {
  name: string;
  score: number;
  evidence: string;
};

export type ScoreResult = {
  overall: number;
  categories: ScoreCategory[];
  engine?: string;
  github_enriched?: boolean;
  jd_match?: {
    matched_keywords?: string[];
    missing_keywords?: string[];
    relevance?: number;
  };
};

export type JobStatus = {
  id?: string;
  job_id: string;
  kind?: string;
  status: "queued" | "processing" | "complete" | "failed" | string;
  result?: ScoreResult | null;
  error?: string | null;
};

export async function getSettings(): Promise<UserSettings> {
  const res = await authed(
    await fetch(`${API}/settings`, { headers: { ...authHeaders() } }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as UserSettings;
}

export async function saveSettings(body: {
  github_username?: string;
}): Promise<UserSettings> {
  const res = await authed(
    await fetch(`${API}/settings`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify(body),
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as UserSettings;
}

export async function updateGithubCache(): Promise<UserSettings> {
  const res = await authed(
    await fetch(`${API}/settings/github/update`, {
      method: "POST",
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as UserSettings;
}

export async function startScore(
  resumeId: string,
  jd?: string,
): Promise<JobStatus> {
  const res = await authed(
    await fetch(`${API}/resumes/${resumeId}/score`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify({ jd: jd || undefined }),
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as JobStatus;
}

export async function getJob(jobId: string): Promise<JobStatus> {
  const res = await authed(
    await fetch(`${API}/jobs/${jobId}`, {
      headers: { ...authHeaders() },
    }),
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as JobStatus;
}


