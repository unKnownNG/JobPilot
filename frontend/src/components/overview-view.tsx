"use client";

import type { JobResponse, ApplicationResponse } from "@/lib/api";

interface Props {
  jobs: JobResponse[];
  apps: ApplicationResponse[];
  jobStats: Record<string, number>;
  appFunnel: Record<string, number>;
}

function StatCard({ label, value, accent, delay }: { label: string; value: number; accent: string; delay: number }) {
  return (
    <div className={`bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in border-t-2 ${accent}`}
      style={{ animationDelay: `${delay}ms` }}>
      <p className="text-xs text-muted-fg font-medium uppercase tracking-wider mb-2">{label}</p>
      <p className="text-4xl font-bold text-fg">{value}</p>
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

export default function OverviewView({ jobs, apps, jobStats, appFunnel }: Props) {
  const total = { jobs: jobs.length, apps: apps.length, interviews: appFunnel.interview || 0, offers: appFunnel.offer || 0 };

  return (
    <div className="space-y-6 max-w-[1200px]">
      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Jobs Discovered" value={total.jobs} accent="border-t-accent" delay={0} />
        <StatCard label="Applications" value={total.apps} accent="border-t-primary" delay={60} />
        <StatCard label="Interviews" value={total.interviews} accent="border-t-success" delay={120} />
        <StatCard label="Offers" value={total.offers} accent="border-t-warning" delay={180} />
      </div>

      {/* Funnel + Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in" style={{ animationDelay: "240ms" }}>
          <h3 className="font-semibold text-sm text-fg mb-5">Application Funnel</h3>
          {total.apps === 0 ? (
            <p className="text-muted-fg text-sm py-10 text-center">No applications yet. Start by adding jobs and applying!</p>
          ) : (
            <div className="space-y-4">
              <FunnelBar label="Applied" count={appFunnel.applied || 0} total={total.apps} bg="bg-primary" />
              <FunnelBar label="Under Review" count={appFunnel.under_review || 0} total={total.apps} bg="bg-accent" />
              <FunnelBar label="Interview" count={total.interviews} total={total.apps} bg="bg-success" />
              <FunnelBar label="Offer" count={total.offers} total={total.apps} bg="bg-warning" />
              <FunnelBar label="Rejected" count={appFunnel.rejected || 0} total={total.apps} bg="bg-danger" />
            </div>
          )}
        </div>

        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in" style={{ animationDelay: "300ms" }}>
          <h3 className="font-semibold text-sm text-fg mb-5">Jobs by Status</h3>
          {total.jobs === 0 ? (
            <p className="text-muted-fg text-sm py-10 text-center">No jobs discovered yet. Add one manually or wait for the Scout agent!</p>
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

      {/* Recent jobs */}
      <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in" style={{ animationDelay: "360ms" }}>
        <h3 className="font-semibold text-sm text-fg mb-4">Recent Jobs</h3>
        {jobs.length === 0 ? (
          <p className="text-muted-fg text-sm text-center py-10">No jobs yet. Use the Jobs tab to add your first one!</p>
        ) : (
          <div className="space-y-1">
            {jobs.slice(0, 5).map((job) => (
              <div key={job.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-muted/40 transition-colors">
                <div className="min-w-0">
                  <p className="font-medium text-sm truncate text-fg">{job.title}</p>
                  <p className="text-xs text-muted-fg mt-0.5">{job.company}{job.location ? ` · ${job.location}` : ""}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-4">
                  {job.relevance_score !== null && (
                    <span className="text-[11px] font-medium bg-primary/15 text-primary px-2.5 py-0.5 rounded-full">{Math.round(job.relevance_score)}%</span>
                  )}
                  <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full capitalize ${
                    job.status === "approved" ? "bg-success/15 text-success"
                    : job.status === "rejected" ? "bg-danger/15 text-danger"
                    : "bg-muted text-muted-fg border border-border"
                  }`}>{job.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
