const API_BASE = "http://localhost:8000/api";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

// --- Auth ---
export interface UserResponse {
  id: string;
  email: string;
  name: string;
  preferences: Record<string, unknown> | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export const auth = {
  register: (email: string, name: string, password: string) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, name, password }),
    }),
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<UserResponse>("/auth/me"),
  update: (data: { name?: string; preferences?: Record<string, unknown> }) =>
    request<UserResponse>("/auth/me", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};

// --- Jobs ---
export interface JobResponse {
  id: string;
  user_id: string;
  title: string;
  company: string;
  location: string | null;
  url: string;
  description: string | null;
  requirements: Record<string, unknown> | null;
  relevance_score: number | null;
  source: string;
  status: string;
  salary_min: number | null;
  salary_max: number | null;
  work_type: string | null;
  discovered_at: string;
}

export const jobs = {
  list: (params?: { status?: string; source?: string; min_score?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.source) query.set("source", params.source);
    if (params?.min_score) query.set("min_score", String(params.min_score));
    return request<JobResponse[]>(`/jobs?${query}`);
  },
  get: (id: string) => request<JobResponse>(`/jobs/${id}`),
  create: (data: {
    title: string;
    company: string;
    url: string;
    location?: string;
    description?: string;
    source?: string;
    salary_min?: number;
    salary_max?: number;
    work_type?: string;
  }) =>
    request<JobResponse>("/jobs", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateStatus: (id: string, status: string) =>
    request<JobResponse>(`/jobs/${id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    }),
  stats: () => request<{ total: number; by_status: Record<string, number> }>("/jobs/stats/summary"),
};

// --- Resumes ---
export interface ResumeResponse {
  id: string;
  user_id: string;
  resume_data: Record<string, unknown>;
  raw_text: string | null;
  is_active: boolean;
  created_at: string;
}

export const resumes = {
  list: () => request<ResumeResponse[]>("/resumes"),
  active: () => request<ResumeResponse>("/resumes/active"),
  create: (resume_data: Record<string, unknown>, raw_text?: string) =>
    request<ResumeResponse>("/resumes", {
      method: "POST",
      body: JSON.stringify({ resume_data, raw_text }),
    }),
  get: (id: string) => request<ResumeResponse>(`/resumes/${id}`),
  delete: (id: string) =>
    request<void>(`/resumes/${id}`, { method: "DELETE" }),
};

// --- Applications ---
export interface ApplicationResponse {
  id: string;
  user_id: string;
  job_posting_id: string;
  tailored_resume_id: string | null;
  status: string;
  status_history: Array<Record<string, unknown>>;
  platform: string | null;
  notes: string | null;
  screenshots: string[];
  applied_at: string | null;
  created_at: string;
  updated_at: string;
}

export const applications = {
  list: (status?: string) => {
    const query = status ? `?status=${status}` : "";
    return request<ApplicationResponse[]>(`/applications${query}`);
  },
  get: (id: string) => request<ApplicationResponse>(`/applications/${id}`),
  update: (id: string, data: { status?: string; notes?: string }) =>
    request<ApplicationResponse>(`/applications/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  analytics: () =>
    request<{
      total_applications: number;
      by_status: Record<string, number>;
      funnel: Record<string, number>;
    }>("/applications/stats/analytics"),
};
