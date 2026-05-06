"use client";

import { useState } from "react";
import { agents, type AgentRun } from "@/lib/api";

interface Props {
  runs: AgentRun[];
  onRefresh: () => void;
}

type AgentStatus = "idle" | "running" | "done" | "error";

function StatusDot({ status }: { status: string }) {
  const cls =
    status === "completed" ? "bg-success" :
    status === "running"   ? "bg-warning animate-pulse" :
    status === "failed"    ? "bg-danger" : "bg-muted-fg";
  return <span className={`inline-block w-2 h-2 rounded-full ${cls}`} />;
}

export default function AgentsView({ runs, onRefresh }: Props) {
  const [scoutStatus,  setScoutStatus]  = useState<AgentStatus>("idle");
  const [tailorStatus, setTailorStatus] = useState<AgentStatus>("idle");
  const [applierStatus, setApplierStatus] = useState<AgentStatus>("idle");
  const [scoutResult,  setScoutResult]  = useState<Record<string, unknown> | null>(null);
  const [tailorResult, setTailorResult] = useState<Record<string, unknown> | null>(null);
  const [applierResult, setApplierResult] = useState<Record<string, unknown> | null>(null);
  const [minScore, setMinScore] = useState(60);
  const [searchTerm, setSearchTerm] = useState("");
  const [maxJobs, setMaxJobs] = useState(25);
  const [maxApps, setMaxApps] = useState(5);

  const triggerScout = async () => {
    setScoutStatus("running");
    setScoutResult(null);
    try {
      const res = await agents.runScout(minScore, searchTerm, maxJobs);
      setScoutResult(res.result);
      setScoutStatus("done");
      onRefresh();
    } catch (e: unknown) {
      setScoutResult({ error: e instanceof Error ? e.message : "Unknown error" });
      setScoutStatus("error");
    }
  };

  const triggerTailor = async () => {
    setTailorStatus("running");
    setTailorResult(null);
    try {
      const res = await agents.runTailor();
      setTailorResult(res.result);
      setTailorStatus("done");
      onRefresh();
    } catch (e: unknown) {
      setTailorResult({ error: e instanceof Error ? e.message : "Unknown error" });
      setTailorStatus("error");
    }
  };

  const triggerApplier = async () => {
    setApplierStatus("running");
    setApplierResult(null);
    try {
      const res = await agents.runApplier(maxApps);
      setApplierResult(res.result);
      setApplierStatus("done");
      onRefresh();
    } catch (e: unknown) {
      setApplierResult({ error: e instanceof Error ? e.message : "Unknown error" });
      setApplierStatus("error");
    }
  };

  const scoutRuns  = runs.filter(r => r.agent_type === "scout");
  const tailorRuns = runs.filter(r => r.agent_type === "tailor");
  const applierRuns = runs.filter(r => r.agent_type === "applier");

  return (
    <div className="space-y-6 max-w-[1000px]">
      {/* Info banner */}
      <div className="bg-primary/8 border border-primary/20 rounded-2xl p-4 flex gap-3">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5 text-primary shrink-0 mt-0.5">
          <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
        </svg>
        <div className="text-sm">
          <p className="font-medium text-fg mb-1">How to use the agents</p>
          <ol className="text-muted-fg space-y-0.5 list-decimal list-inside">
            <li>Make sure your <strong className="text-fg">Resume</strong> is saved in the Resume tab.</li>
            <li>Run the <strong className="text-fg">Scout Agent</strong> — it finds & scores remote jobs for you.</li>
            <li>Go to <strong className="text-fg">Jobs</strong> tab — review and <em>Approve</em> the ones you like.</li>
            <li>Run the <strong className="text-fg">Tailor Agent</strong> — it rewrites your resume for each approved job.</li>
            <li>Check the <strong className="text-fg">Applications</strong> tab to see tailored resumes ready to send.</li>
          </ol>
        </div>
      </div>

      {/* Agent cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Scout Agent */}
        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-xl bg-accent/15 flex items-center justify-center">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4 text-accent">
                    <path d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"/>
                  </svg>
                </div>
                <h3 className="font-semibold text-fg">Scout Agent</h3>
              </div>
              <p className="text-xs text-muted-fg">Scrapes LinkedIn, Indeed, Glassdoor & ZipRecruiter, then AI-scores against your resume.</p>
            </div>
            <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full capitalize ${
              scoutStatus === "running" ? "bg-warning/15 text-warning" :
              scoutStatus === "done"    ? "bg-success/15 text-success" :
              scoutStatus === "error"   ? "bg-danger/15 text-danger" :
              "bg-muted text-muted-fg border border-border"
            }`}>{scoutStatus}</span>
          </div>

          <div className="space-y-2">
            <div>
              <label className="text-xs text-muted-fg font-medium block mb-1">Min relevance score: <span className="text-fg font-semibold">{minScore}%</span></label>
              <input type="range" min="40" max="90" value={minScore} onChange={e => setMinScore(Number(e.target.value))}
                className="w-full accent-primary cursor-pointer" />
            </div>
            <div>
              <label className="text-xs text-muted-fg font-medium block mb-1">Search query <span className="text-muted-fg/60">(blank = uses your resume title)</span></label>
              <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="e.g. Python developer, React engineer..."
                className="w-full px-3 py-2 rounded-xl bg-muted border border-border text-sm text-fg outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all" />
            </div>
            <div>
              <label className="text-xs text-muted-fg font-medium block mb-1">Max jobs to fetch: <span className="text-fg font-semibold">{maxJobs}</span></label>
              <input type="range" min="10" max="50" value={maxJobs} onChange={e => setMaxJobs(Number(e.target.value))}
                className="w-full accent-primary cursor-pointer" />
            </div>
          </div>

          <button onClick={triggerScout} disabled={scoutStatus === "running"}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-primary to-[#6c5ce7] text-white text-sm font-medium disabled:opacity-50 hover:shadow-lg hover:shadow-primary/20 transition-all cursor-pointer">
            {scoutStatus === "running" ? "🔍 Scanning jobs..." : "Run Scout Agent"}
          </button>

          {scoutResult && (
            <div className={`rounded-xl p-3 text-xs space-y-1 ${scoutResult.error ? "bg-danger/10 border border-danger/20 text-danger" : "bg-success/10 border border-success/20 text-success"}`}>
              {scoutResult.error ? (
                <p>{String(scoutResult.error)}</p>
              ) : (
                <>
                  <div className="grid grid-cols-3 gap-2">
                    {Object.entries(scoutResult).map(([k, v]) => (
                      <div key={k} className="text-center">
                        <p className="text-lg font-bold text-fg">{String(v)}</p>
                        <p className="text-muted-fg capitalize">{k}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {scoutRuns.length > 0 && (
            <div className="pt-2 border-t border-border">
              <p className="text-[11px] text-muted-fg font-medium mb-2">Last {Math.min(scoutRuns.length, 3)} runs</p>
              {scoutRuns.slice(0, 3).map(r => (
                <div key={r.id} className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2">
                    <StatusDot status={r.status} />
                    <span className="text-xs text-muted-fg capitalize">{r.status}</span>
                  </div>
                  <span className="text-[11px] text-muted-fg">
                    {r.result ? `${r.result.saved ?? 0} saved` : "—"} · {r.started_at ? new Date(r.started_at).toLocaleTimeString() : ""}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tailor Agent */}
        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-xl bg-success/15 flex items-center justify-center">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4 text-success">
                    <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                  </svg>
                </div>
                <h3 className="font-semibold text-fg">Tailor Agent</h3>
              </div>
              <p className="text-xs text-muted-fg">Rewrites your resume bullets to perfectly match each approved job description.</p>
            </div>
            <span className={`text-[11px] font-medium px-2.5 py-1 rounded-full capitalize ${
              tailorStatus === "running" ? "bg-warning/15 text-warning" :
              tailorStatus === "done"    ? "bg-success/15 text-success" :
              tailorStatus === "error"   ? "bg-danger/15 text-danger" :
              "bg-muted text-muted-fg border border-border"
            }`}>{tailorStatus}</span>
          </div>

          <div className="bg-muted rounded-xl p-3 text-xs text-muted-fg space-y-1.5">
            <p className="font-medium text-fg text-[13px]">What this agent does:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Finds all your <span className="text-fg">Approved</span> jobs</li>
              <li>Reads your master resume from the database</li>
              <li>Rewrites experience bullets to match the job</li>
              <li>Reorders skills (most relevant first)</li>
              <li>Creates an Application with status <span className="text-success">resume_ready</span></li>
            </ul>
          </div>

          <button onClick={triggerTailor} disabled={tailorStatus === "running"}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-success/80 to-success text-white text-sm font-medium disabled:opacity-50 hover:shadow-lg hover:shadow-success/20 transition-all cursor-pointer">
            {tailorStatus === "running" ? "✍️ Tailoring resumes..." : "Run Tailor Agent"}
          </button>

          {tailorResult && (
            <div className={`rounded-xl p-3 text-xs ${tailorResult.error ? "bg-danger/10 border border-danger/20 text-danger" : "bg-success/10 border border-success/20 text-success"}`}>
              {tailorResult.error ? (
                <p>{String(tailorResult.error)}</p>
              ) : (
                <div className="grid grid-cols-3 gap-2 text-center">
                  {Object.entries(tailorResult).map(([k, v]) => (
                    <div key={k}>
                      <p className="text-lg font-bold text-fg">{String(v)}</p>
                      <p className="text-muted-fg capitalize">{k}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {tailorRuns.length > 0 && (
            <div className="pt-2 border-t border-border">
              <p className="text-[11px] text-muted-fg font-medium mb-2">Last {Math.min(tailorRuns.length, 3)} runs</p>
              {tailorRuns.slice(0, 3).map(r => (
                <div key={r.id} className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2">
                    <StatusDot status={r.status} />
                    <span className="text-xs text-muted-fg capitalize">{r.status}</span>
                  </div>
                  <span className="text-[11px] text-muted-fg">
                    {r.result ? `${r.result.tailored ?? 0} tailored` : "—"} · {r.started_at ? new Date(r.started_at).toLocaleTimeString() : ""}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Applier Agent — full width */}
      <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-8 h-8 rounded-xl bg-warning/15 flex items-center justify-center">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4 text-warning">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>
                </svg>
              </div>
              <h3 className="font-semibold text-fg">Applier Agent</h3>
            </div>
            <p className="text-xs text-muted-fg">Uses your Chrome Extension to fill job applications from inside your real logged-in browser — no bots, no CAPTCHAs.</p>
          </div>
          <span className="text-[11px] font-medium px-2.5 py-1 rounded-full bg-accent/15 text-accent border border-accent/20">Extension-Based</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-muted rounded-xl p-3 text-xs text-muted-fg space-y-1.5">
            <p className="font-medium text-fg text-[13px]">How it works:</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Open any job application page in Chrome</li>
              <li>Click the <span className="text-fg font-medium">JobPilot Extension</span> icon</li>
              <li>Extension scrapes form fields from the page</li>
              <li>AI maps your resume data → each form field</li>
              <li>Extension fills the form instantly in your session</li>
              <li>Application is logged to the <span className="text-fg">Applications</span> tab</li>
            </ol>
          </div>
          <div className="bg-muted rounded-xl p-3 text-xs text-muted-fg space-y-1.5">
            <p className="font-medium text-fg text-[13px]">Why extension beats headless browser:</p>
            <ul className="space-y-1">
              {[
                ["✅", "Already logged in to LinkedIn, Indeed, etc."],
                ["✅", "No CAPTCHA or bot-detection issues"],
                ["✅", "Works on React / Angular / Vue job sites"],
                ["✅", "Human-in-the-loop — you verify before submitting"],
                ["✅", "No Playwright crashes on Windows"],
              ].map(([icon, text]) => (
                <li key={text as string} className="flex items-start gap-1.5">
                  <span>{icon}</span><span>{text}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* API Endpoints the extension calls */}
        <div className="bg-muted/50 border border-border rounded-xl p-3">
          <p className="text-xs font-medium text-fg mb-2.5">Backend endpoints (ready now):</p>
          <div className="space-y-1.5">
            {[
              { method: "GET",  path: "/api/agents/applier/autofill-data", desc: "Fetch flat resume data for filling" },
              { method: "POST", path: "/api/agents/applier/analyze-form",  desc: "AI maps form fields → resume values" },
              { method: "POST", path: "/api/agents/applier/log",           desc: "Log completed application to dashboard" },
            ].map(ep => (
              <div key={ep.path} className="flex items-center gap-2 text-xs">
                <span className={`font-mono font-bold px-1.5 py-0.5 rounded text-[10px] shrink-0 ${
                  ep.method === "GET" ? "bg-success/15 text-success" : "bg-primary/15 text-primary"
                }`}>{ep.method}</span>
                <code className="text-muted-fg font-mono text-[11px] truncate">{ep.path}</code>
                <span className="text-muted-fg/50 ml-auto hidden sm:block shrink-0">{ep.desc}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent runs */}
        {applierRuns.length > 0 ? (
          <div className="pt-2 border-t border-border">
            <p className="text-[11px] text-muted-fg font-medium mb-2">Recent extension runs</p>
            {applierRuns.slice(0, 5).map(r => (
              <div key={r.id} className="flex items-center justify-between py-1.5">
                <div className="flex items-center gap-2">
                  <StatusDot status={r.status} />
                  <span className="text-xs text-muted-fg capitalize">{r.status}</span>
                  {r.result?.job_title && (
                    <span className="text-xs text-fg font-medium">
                      {String(r.result.job_title)}{r.result.company ? ` @ ${r.result.company}` : ""}
                    </span>
                  )}
                </div>
                <span className="text-[11px] text-muted-fg">
                  {Array.isArray(r.result?.fields_filled)
                    ? `${r.result.fields_filled.length} fields filled`
                    : "—"
                  } · {r.started_at ? new Date(r.started_at).toLocaleTimeString() : ""}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-xs text-muted-fg/50 py-3">
            No applications logged yet — install the Chrome Extension to start applying!
          </p>
        )}
      </div>

      {/* Full run history */}

      {runs.length > 0 && (
        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20">
          <h3 className="font-semibold text-sm text-fg mb-4">Full Agent Run History</h3>
          <div className="space-y-1">
            {runs.map((r, i) => (
              <div key={r.id}
                className="flex items-center justify-between p-3 rounded-xl hover:bg-muted/40 transition-colors animate-fade-in"
                style={{ animationDelay: `${i * 30}ms` }}>
                <div className="flex items-center gap-3">
                  <StatusDot status={r.status} />
                  <div>
                    <span className="text-sm font-medium text-fg capitalize">{r.agent_type} Agent</span>
                    <span className={`ml-2 text-[11px] px-2 py-0.5 rounded-full capitalize ${
                      r.status === "completed" ? "bg-success/15 text-success" :
                      r.status === "running"   ? "bg-warning/15 text-warning" :
                      r.status === "failed"    ? "bg-danger/15 text-danger" :
                      "bg-muted text-muted-fg"}`}>{r.status}</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-muted-fg">
                    {r.result && !r.result.error
                      ? Object.entries(r.result).map(([k,v]) => `${v} ${k}`).join(" · ")
                      : r.result?.error ? "Failed" : "—"}
                  </p>
                  <p className="text-[11px] text-muted-fg/60">
                    {r.started_at ? new Date(r.started_at).toLocaleString() : ""}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
