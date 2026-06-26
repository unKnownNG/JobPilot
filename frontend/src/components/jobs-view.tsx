"use client";

import { useState, useEffect, useRef } from "react";
import { jobs as jobsApi, type JobResponse } from "@/lib/api";

interface Props {
  jobs: JobResponse[];
  onRefresh: () => void;
}

// ─── Resume Prompt Modal ──────────────────────────────────────────────────────

interface ModalProps {
  job: JobResponse;
  onClose: () => void;
}

function ResumePromptModal({ job, onClose }: ModalProps) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    jobsApi.generateTailorPrompt(job.id)
      .then((res) => { if (!cancelled) setPrompt(res.prompt); })
      .catch((err) => { if (!cancelled) setError(err instanceof Error ? err.message : "Failed to generate prompt"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [job.id]);

  const handleCopy = async () => {
    const text = prompt;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      textareaRef.current?.select();
      document.execCommand("copy");
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  // Close on backdrop click
  const handleBackdrop = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(6px)" }}
      onClick={handleBackdrop}
    >
      <div
        className="relative w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl border border-border overflow-hidden animate-fade-in"
        style={{
          background: "linear-gradient(145deg, hsl(var(--card)) 0%, hsl(var(--bg)) 100%)",
          boxShadow: "0 32px 64px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)",
        }}
      >
        {/* Decorative glows */}
        <div className="absolute -top-24 -right-24 w-56 h-56 rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, hsl(var(--primary)/0.15) 0%, transparent 70%)" }} />
        <div className="absolute -bottom-20 -left-20 w-40 h-40 rounded-full pointer-events-none" style={{ background: "radial-gradient(circle, hsl(var(--accent)/0.12) 0%, transparent 70%)" }} />

        {/* Header */}
        <div className="relative flex items-start justify-between gap-4 px-6 py-5 border-b border-border shrink-0">
          <div className="flex items-center gap-3">
            {/* Wand icon */}
            <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0" style={{ background: "linear-gradient(135deg, hsl(var(--primary)/0.2), hsl(var(--accent)/0.2))", border: "1px solid hsl(var(--primary)/0.25)" }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5 text-primary">
                <path d="M15 4V2M15 16v-2M8 9h2M20 9h2M17.8 11.8 19 13M17.8 6.2 19 5M3 21l9-9M12.2 6.2 11 5" />
                <path d="m5 3 1 1M19 19l-1-1" />
              </svg>
            </div>
            <div>
              <h2 className="font-semibold text-fg text-base leading-tight">Tailor Resume for This Job</h2>
              <p className="text-xs text-muted-fg mt-0.5">
                <span className="text-fg font-medium">{job.title}</span>
                {" · "}
                <span>{job.company}</span>
                {job.location ? ` · ${job.location}` : ""}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-muted-fg hover:text-fg transition rounded-lg p-1 hover:bg-muted cursor-pointer shrink-0 mt-0.5"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Instructions banner */}
        <div className="relative px-6 py-3 flex items-center gap-2.5 text-xs border-b border-border shrink-0" style={{ background: "hsl(var(--primary)/0.06)" }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4 text-primary shrink-0">
            <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
          </svg>
          <p className="text-muted-fg leading-relaxed">
            Copy this AI-generated prompt → open <span className="text-fg font-medium">Claude.ai</span> → paste the prompt + your LaTeX resume → get a perfectly tailored resume
          </p>
        </div>

        {/* Content */}
        <div className="relative flex-1 overflow-hidden flex flex-col min-h-0">
          {loading ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-4 p-12">
              {/* Animated ring */}
              <div className="relative w-14 h-14">
                <div className="absolute inset-0 rounded-full border-2 border-primary/20" />
                <div className="absolute inset-0 rounded-full border-2 border-t-primary animate-spin" />
                <div className="absolute inset-2 rounded-full border border-accent/30 animate-ping" style={{ animationDuration: "2s" }} />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-fg">Claude Sonnet is analysing this job…</p>
                <p className="text-xs text-muted-fg mt-1">Crafting a precise resume tailoring prompt</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 p-12 text-center">
              <div className="w-12 h-12 rounded-2xl bg-danger/10 flex items-center justify-center">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6 text-danger">
                  <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
                </svg>
              </div>
              <p className="text-sm text-danger font-medium">{error}</p>
              <button
                onClick={() => {
                  setError("");
                  setLoading(true);
                  jobsApi.generateTailorPrompt(job.id)
                    .then((res) => setPrompt(res.prompt))
                    .catch((err) => setError(err instanceof Error ? err.message : "Failed to generate prompt"))
                    .finally(() => setLoading(false));
                }}
                className="text-xs px-4 py-2 rounded-lg bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition cursor-pointer"
              >
                Try Again
              </button>
            </div>
          ) : (
            <>
              {/* Prompt textarea */}
              <div className="flex-1 overflow-auto p-5 min-h-0">
                <textarea
                  ref={textareaRef}
                  readOnly
                  value={prompt}
                  className="w-full h-full min-h-[320px] resize-none rounded-xl px-4 py-3.5 text-sm font-mono leading-relaxed outline-none"
                  style={{
                    background: "hsl(var(--bg))",
                    border: "1px solid hsl(var(--border))",
                    color: "hsl(var(--fg))",
                    caretColor: "transparent",
                  }}
                  spellCheck={false}
                />
              </div>

              {/* Footer actions */}
              <div className="relative px-5 py-4 border-t border-border flex items-center justify-between gap-3 shrink-0">
                <p className="text-xs text-muted-fg">
                  {prompt.split(/\s+/).length} words · generated by Claude Sonnet via Pollinations AI
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={onClose}
                    className="text-xs px-4 py-2 rounded-lg bg-muted text-muted-fg border border-border hover:text-fg transition cursor-pointer"
                  >
                    Close
                  </button>
                  <button
                    onClick={handleCopy}
                    className="relative text-xs px-5 py-2 rounded-lg font-semibold text-white cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/25 active:translate-y-0 overflow-hidden"
                    style={{ background: "linear-gradient(135deg, hsl(var(--primary)), #6c5ce7)" }}
                  >
                    <span className={`flex items-center gap-1.5 transition-all ${copied ? "opacity-0 scale-90" : "opacity-100 scale-100"}`}>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="w-3.5 h-3.5">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                        <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
                      </svg>
                      Copy Prompt
                    </span>
                    {copied && (
                      <span className="absolute inset-0 flex items-center justify-center gap-1.5">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="w-3.5 h-3.5">
                          <path d="M20 6L9 17l-5-5" />
                        </svg>
                        Copied!
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}


// ─── Jobs View ────────────────────────────────────────────────────────────────

export default function JobsView({ jobs: jobList, onRefresh }: Props) {
  const [showAdd, setShowAdd] = useState(false);
  const [filter, setFilter] = useState("");
  const [form, setForm] = useState({
    title: "", company: "", url: "", location: "",
    description: "", work_type: "remote", source: "manual",
  });
  const [loading, setLoading] = useState(false);

  // Import URL state
  const [importUrl, setImportUrl] = useState("");
  const [importLoading, setImportLoading] = useState(false);
  const [importResult, setImportResult] = useState<JobResponse | null>(null);
  const [importError, setImportError] = useState("");

  // Tailor resume modal state
  const [tailorJob, setTailorJob] = useState<JobResponse | null>(null);

  const filtered = filter ? jobList.filter((j) => j.status === filter) : jobList;

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await jobsApi.create(form);
      setShowAdd(false);
      setForm({ title: "", company: "", url: "", location: "", description: "", work_type: "remote", source: "manual" });
      onRefresh();
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleImportUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importUrl.trim()) return;
    setImportLoading(true);
    setImportResult(null);
    setImportError("");
    try {
      const job = await jobsApi.importUrl(importUrl.trim());
      setImportResult(job);
      setImportUrl("");
      onRefresh();
    } catch (err) {
      setImportError(err instanceof Error ? err.message : "Failed to import job");
    } finally {
      setImportLoading(false);
    }
  };

  const updateStatus = async (id: string, status: string) => {
    await jobsApi.updateStatus(id, status);
    onRefresh();
  };

  const inputCls = "w-full px-3.5 py-2.5 rounded-xl bg-muted border border-border text-sm text-fg placeholder:text-muted-fg/50 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all";

  return (
    <div className="space-y-5 max-w-[1200px]">

      {/* Tailor Resume Modal */}
      {tailorJob && (
        <ResumePromptModal job={tailorJob} onClose={() => setTailorJob(null)} />
      )}

      {/* ── Import from URL ── */}
      <div className="relative overflow-hidden bg-gradient-to-br from-primary/8 via-card to-accent/5 border border-primary/20 rounded-2xl p-6 shadow-lg shadow-primary/5">
        {/* Decorative glow */}
        <div className="absolute -top-20 -right-20 w-48 h-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-16 -left-16 w-36 h-36 bg-accent/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-9 h-9 rounded-xl bg-primary/15 flex items-center justify-center ring-1 ring-primary/20">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-[18px] h-[18px] text-primary">
                <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71" />
                <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-sm text-fg">Import Job from URL</h3>
              <p className="text-xs text-muted-fg">Paste a job link — AI extracts details, scores it, and auto-approves it for all agents</p>
            </div>
          </div>

          <form onSubmit={handleImportUrl} className="flex gap-2.5">
            <div className="flex-1 relative">
              <input
                type="url"
                placeholder="https://linkedin.com/jobs/view/... or any job board link"
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                required
                disabled={importLoading}
                className="w-full px-4 py-3 rounded-xl bg-bg/80 backdrop-blur-sm border border-border text-sm text-fg placeholder:text-muted-fg/40 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all disabled:opacity-50"
              />
              {importLoading && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="w-5 h-5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                </div>
              )}
            </div>
            <button
              type="submit"
              disabled={importLoading || !importUrl.trim()}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-primary to-[#6c5ce7] text-white text-sm font-semibold disabled:opacity-40 hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-0.5 active:translate-y-0 transition-all cursor-pointer shrink-0"
            >
              {importLoading ? (
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                  </svg>
                  Importing…
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="w-4 h-4">
                    <path d="M12 5v14M5 12h14" />
                  </svg>
                  Import &amp; Process
                </span>
              )}
            </button>
          </form>

          {/* Import success */}
          {importResult && (
            <div className="mt-3 bg-success/8 border border-success/20 rounded-xl p-4 animate-fade-in">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-success/15 flex items-center justify-center shrink-0 mt-0.5">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="w-4 h-4 text-success">
                    <path d="M20 6L9 17l-5-5" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-fg">{importResult.title}</p>
                  <p className="text-xs text-muted-fg mt-0.5">
                    {importResult.company}
                    {importResult.location ? ` · ${importResult.location}` : ""}
                    {importResult.work_type ? ` · ${importResult.work_type}` : ""}
                  </p>
                  <div className="flex items-center gap-3 mt-2">
                    {importResult.relevance_score !== null && (
                      <span className="text-xs font-medium bg-primary/10 text-primary px-2.5 py-1 rounded-full">
                        {Math.round(importResult.relevance_score)}% match
                      </span>
                    )}
                    <span className="text-xs font-medium bg-success/10 text-success px-2.5 py-1 rounded-full capitalize">
                      {importResult.status}
                    </span>
                    <span className="text-xs text-muted-fg">Ready for Tailor &amp; Applier agents</span>
                  </div>
                </div>
                <button onClick={() => setImportResult(null)} className="text-muted-fg hover:text-fg transition cursor-pointer">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4"><path d="M18 6L6 18M6 6l12 12" /></svg>
                </button>
              </div>
            </div>
          )}

          {/* Import error */}
          {importError && (
            <div className="mt-3 bg-danger/8 border border-danger/20 rounded-xl p-3 flex items-center gap-2.5 animate-fade-in">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4 text-danger shrink-0">
                <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
              </svg>
              <p className="text-xs text-danger flex-1">{importError}</p>
              <button onClick={() => setImportError("")} className="text-danger/60 hover:text-danger transition cursor-pointer">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-3.5 h-3.5"><path d="M18 6L6 18M6 6l12 12" /></svg>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex gap-2 flex-wrap">
          {["", "discovered", "approved", "rejected", "applied"].map((s) => (
            <button key={s} onClick={() => setFilter(s)}
              className={`text-xs px-3.5 py-1.5 rounded-full font-medium capitalize cursor-pointer transition-all ${
                filter === s
                  ? "bg-primary text-white shadow-md shadow-primary/25"
                  : "bg-muted text-muted-fg border border-border hover:border-primary/30 hover:text-fg"
              }`}>
              {s || "All"}
            </button>
          ))}
        </div>
        <button onClick={() => setShowAdd(!showAdd)}
          className="text-sm px-5 py-2 rounded-xl bg-gradient-to-r from-primary to-[#6c5ce7] text-white font-medium hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-0.5 transition-all cursor-pointer">
          + Add Job
        </button>
      </div>

      {/* Add form */}
      {showAdd && (
        <form onSubmit={handleAdd} className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 space-y-4 animate-fade-in">
          <h3 className="font-semibold text-sm text-fg">Add New Job</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input placeholder="Job Title *" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className={inputCls} />
            <input placeholder="Company *" required value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} className={inputCls} />
            <input placeholder="Job URL *" required type="url" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className={inputCls} />
            <input placeholder="Location" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} className={inputCls} />
            <select value={form.work_type} onChange={(e) => setForm({ ...form, work_type: e.target.value })} className={inputCls}>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">On-site</option>
            </select>
            <select value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} className={inputCls}>
              <option value="manual">Manual</option>
              <option value="linkedin">LinkedIn</option>
              <option value="indeed">Indeed</option>
              <option value="glassdoor">Glassdoor</option>
            </select>
          </div>
          <textarea placeholder="Paste the job description here..." value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })} rows={4} className={`${inputCls} resize-none`} />
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={() => setShowAdd(false)}
              className="text-sm px-4 py-2 rounded-xl bg-muted text-muted-fg border border-border hover:text-fg transition cursor-pointer">Cancel</button>
            <button type="submit" disabled={loading}
              className="text-sm px-5 py-2 rounded-xl bg-gradient-to-r from-primary to-[#6c5ce7] text-white font-medium disabled:opacity-50 transition cursor-pointer">
              {loading ? "Saving..." : "Save Job"}
            </button>
          </div>
        </form>
      )}

      {/* Job list */}
      {filtered.length === 0 ? (
        <div className="bg-card border border-border rounded-2xl p-16 text-center shadow-lg shadow-black/20">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-10 h-10 mx-auto mb-3 text-muted-fg/40">
            <path d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" />
          </svg>
          <p className="text-sm text-muted-fg">No jobs found. Import a URL or add one to get started!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((job, i) => (
            <div key={job.id}
              className="bg-card border border-border rounded-2xl p-4 shadow-md shadow-black/15 flex items-center justify-between animate-fade-in hover:border-primary/25 transition-colors"
              style={{ animationDelay: `${i * 40}ms` }}>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2.5 mb-1">
                  <h3 className="font-medium text-sm truncate text-fg">{job.title}</h3>
                  {job.source === "user_link" && (
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-accent/10 text-accent border border-accent/15">imported</span>
                  )}
                  <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full capitalize ${
                    job.status === "approved" ? "bg-success/15 text-success"
                    : job.status === "rejected" ? "bg-danger/15 text-danger"
                    : job.status === "applied" ? "bg-primary/15 text-primary"
                    : "bg-muted text-muted-fg border border-border"
                  }`}>{job.status}</span>
                </div>
                <p className="text-xs text-muted-fg">
                  {job.company}{job.location ? ` · ${job.location}` : ""}{job.work_type ? ` · ${job.work_type}` : ""}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-4">
                {job.relevance_score !== null && (
                  <span className="text-[11px] font-medium bg-primary/10 text-primary px-2.5 py-0.5 rounded-full">{Math.round(job.relevance_score)}%</span>
                )}
                {job.status === "discovered" && (
                  <>
                    <button onClick={() => updateStatus(job.id, "approved")}
                      className="text-xs px-3 py-1.5 rounded-lg bg-success/10 text-success border border-success/20 hover:bg-success/20 transition cursor-pointer font-medium">Approve</button>
                    <button onClick={() => updateStatus(job.id, "rejected")}
                      className="text-xs px-3 py-1.5 rounded-lg bg-danger/10 text-danger border border-danger/20 hover:bg-danger/20 transition cursor-pointer font-medium">Reject</button>
                  </>
                )}

                {/* Tailor Resume button */}
                <button
                  onClick={() => setTailorJob(job)}
                  title="Generate a Claude resume-tailoring prompt for this job"
                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer hover:-translate-y-0.5 hover:shadow-md"
                  style={{
                    background: "linear-gradient(135deg, hsl(var(--primary)/0.12), hsl(var(--accent)/0.12))",
                    border: "1px solid hsl(var(--primary)/0.25)",
                    color: "hsl(var(--primary))",
                  }}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                    <path d="M15 4V2M15 16v-2M8 9h2M20 9h2M17.8 11.8 19 13M17.8 6.2 19 5M3 21l9-9M12.2 6.2 11 5" />
                  </svg>
                  Tailor
                </button>

                <a href={job.url} target="_blank" rel="noopener noreferrer"
                  className="text-xs px-3 py-1.5 rounded-lg bg-muted text-muted-fg border border-border hover:text-fg transition font-medium">Open</a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
