"use client";

import type { JobResponse, ApplicationResponse, AgentRun } from "@/lib/api";

interface Props {
  jobs: JobResponse[];
  apps: ApplicationResponse[];
  jobStats: Record<string, number>;
  appFunnel: Record<string, number>;
  agentRuns: AgentRun[];
  onNavigate: (tab: "jobs" | "applications" | "agents" | "resume" | "overview") => void;
}

function StatCard({ label, value, accent, sub, delay }: { label: string; value: number; accent: string; sub?: string; delay: number }) {
  return (
    <div className={`bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in border-t-2 ${accent}`}
      style={{ animationDelay: `${delay}ms` }}>
      <p className="text-xs text-muted-fg font-medium uppercase tracking-wider mb-2">{label}</p>
      <p className="text-4xl font-bold text-fg">{value}</p>
      {sub && <p className="text-xs text-muted-fg mt-1">{sub}</p>}
    </div>
  );
}

function FunnelBar({ label, count, total, bg }: { label: string; count: number; total: number; bg: string }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span className="text-muted-fg">{label}</span>
        <span className="font-semibold text-fg">{count}</span>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${bg} transition-all duration-700`} style={{ width: `${Math.max(pct, 3)}%` }} />
      </div>
    </div>
  );
}

export default function OverviewView({ jobs, apps, jobStats, appFunnel, agentRuns, onNavigate }: Props) {
  const total = {
    jobs: jobs.length,
    apps: apps.length,
    interviews: appFunnel.interview_scheduled || 0,
    offers: appFunnel.offer_received || 0,
  };
  const pendingJobs   = jobs.filter(j => j.status === "discovered").length;
  const readyApps     = apps.filter(a => a.status === "resume_ready").length;
  const lastScoutRun  = agentRuns.find(r => r.agent_type === "scout");
  const lastTailorRun = agentRuns.find(r => r.agent_type === "tailor");

  return (
    <div className="space-y-6 max-w-[1200px]">
      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Jobs Discovered" value={total.jobs} accent="border-t-accent" delay={0}
          sub={pendingJobs > 0 ? `${pendingJobs} pending review` : "All reviewed"} />
        <StatCard label="Applications" value={total.apps} accent="border-t-primary" delay={60}
          sub={readyApps > 0 ? `${readyApps} ready to send` : undefined} />
        <StatCard label="Interviews" value={total.interviews} accent="border-t-success" delay={120} />
        <StatCard label="Offers" value={total.offers} accent="border-t-warning" delay={180} />
      </div>

      {/* Pending actions banner */}
      {(pendingJobs > 0 || readyApps > 0) && (
        <div className="flex flex-wrap gap-3 animate-fade-in" style={{ animationDelay: "200ms" }}>
          {pendingJobs > 0 && (
            <button onClick={() => onNavigate("jobs")}
              className="flex items-center gap-2 bg-warning/10 border border-warning/25 rounded-xl px-4 py-3 text-sm text-warning hover:bg-warning/15 transition cursor-pointer">
              <span className="font-bold">{pendingJobs}</span> jobs waiting for your review →
            </button>
          )}
          {readyApps > 0 && (
            <button onClick={() => onNavigate("applications")}
              className="flex items-center gap-2 bg-success/10 border border-success/25 rounded-xl px-4 py-3 text-sm text-success hover:bg-success/15 transition cursor-pointer">
              <span className="font-bold">{readyApps}</span> tailored resumes ready to apply →
            </button>
          )}
        </div>
      )}

      {/* Funnel + Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in" style={{ animationDelay: "240ms" }}>
          <h3 className="font-semibold text-sm text-fg mb-5">Application Funnel</h3>
          {total.apps === 0 ? (
            <div className="text-center py-10">
              <p className="text-muted-fg text-sm">No applications yet.</p>
              <button onClick={() => onNavigate("agents")} className="mt-3 text-xs text-primary hover:underline cursor-pointer">
                Run the Scout Agent to find jobs →
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <FunnelBar label="Applied"       count={appFunnel.applied || 0}          total={total.apps} bg="bg-primary" />
              <FunnelBar label="Under Review"  count={appFunnel.under_review || 0}     total={total.apps} bg="bg-accent" />
              <FunnelBar label="Interview"     count={total.interviews}                total={total.apps} bg="bg-success" />
              <FunnelBar label="Offer"         count={total.offers}                    total={total.apps} bg="bg-warning" />
              <FunnelBar label="Rejected"      count={appFunnel.rejected || 0}         total={total.apps} bg="bg-danger" />
            </div>
          )}
        </div>

        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in" style={{ animationDelay: "300ms" }}>
          <h3 className="font-semibold text-sm text-fg mb-5">Jobs by Status</h3>
          {total.jobs === 0 ? (
            <div className="text-center py-10">
              <p className="text-muted-fg text-sm">No jobs yet.</p>
              <button onClick={() => onNavigate("agents")} className="mt-3 text-xs text-primary hover:underline cursor-pointer">
                Run the Scout Agent →
              </button>
            </div>
          ) : (
            <div className="space-y-1">
              {Object.entries(jobStats).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between py-2.5 px-3 rounded-xl hover:bg-muted/60 transition-colors">
                  <span className="text-sm capitalize text-muted-fg">{status.replace(/_/g, " ")}</span>
                  <span className="text-sm font-semibold bg-muted text-fg px-2.5 py-0.5 rounded-full border border-border">{count}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Agent status + Recent jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Agent quick status */}
        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in" style={{ animationDelay: "320ms" }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm text-fg">AI Agents</h3>
            <button onClick={() => onNavigate("agents")} className="text-xs text-primary hover:underline cursor-pointer">Manage →</button>
          </div>
          <div className="space-y-3">
            {[
              { name: "Scout Agent",  run: lastScoutRun,  color: "bg-accent/15 text-accent" },
              { name: "Tailor Agent", run: lastTailorRun, color: "bg-success/15 text-success" },
            ].map(({ name, run, color }) => (
              <div key={name} className="flex items-center justify-between p-3 bg-muted/40 rounded-xl">
                <span className="text-sm text-fg">{name}</span>
                {run ? (
                  <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full capitalize ${
                    run.status === "completed" ? "bg-success/15 text-success" :
                    run.status === "failed"    ? "bg-danger/15 text-danger" :
                    "bg-warning/15 text-warning"
                  }`}>{run.status}</span>
                ) : (
                  <span className="text-[11px] text-muted-fg bg-muted border border-border px-2 py-0.5 rounded-full">never run</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Recent jobs */}
        <div className="lg:col-span-2 bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in" style={{ animationDelay: "360ms" }}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm text-fg">Recent Jobs</h3>
            <button onClick={() => onNavigate("jobs")} className="text-xs text-primary hover:underline cursor-pointer">View all →</button>
          </div>
          {jobs.length === 0 ? (
            <p className="text-muted-fg text-sm text-center py-8">No jobs yet. Run the Scout Agent to discover some!</p>
          ) : (
            <div className="space-y-1">
              {jobs.slice(0, 6).map((job) => (
                <div key={job.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-muted/40 transition-colors">
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate text-fg">{job.title}</p>
                    <p className="text-xs text-muted-fg mt-0.5">{job.company}{job.location ? ` · ${job.location}` : ""}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-4">
                    {job.relevance_score != null && (
                      <span className="text-[11px] font-medium bg-primary/15 text-primary px-2.5 py-0.5 rounded-full">{Math.round(job.relevance_score)}%</span>
                    )}
                    <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full capitalize ${
                      job.status === "approved" ? "bg-success/15 text-success" :
                      job.status === "rejected" ? "bg-danger/15 text-danger" :
                      "bg-muted text-muted-fg border border-border"
                    }`}>{job.status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
