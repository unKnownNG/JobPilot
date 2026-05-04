"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { jobs, applications, agents, type JobResponse, type ApplicationResponse, type AgentRun } from "@/lib/api";
import JobsView from "@/components/jobs-view";
import ApplicationsView from "@/components/applications-view";
import ResumeView from "@/components/resume-view";
import OverviewView from "@/components/overview-view";
import AgentsView from "@/components/agents-view";

const NAV = [
  { id: "overview",     label: "Overview",     d: "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z" },
  { id: "jobs",         label: "Jobs",         d: "M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z" },
  { id: "applications", label: "Applications", d: "M22 2L11 13M22 2l-7 20-4-9-9-4z" },
  { id: "resume",       label: "Resume",       d: "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6M16 13H8M16 17H8M10 9H8" },
  { id: "agents",       label: "AI Agents",    d: "M12 2a5 5 0 015 5v3a5 5 0 01-10 0V7a5 5 0 015-5zM4 20c0-4 3.6-7 8-7s8 3 8 7" },
] as const;
type Tab = (typeof NAV)[number]["id"];

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState<Tab>("overview");
  const [jobList, setJobList]     = useState<JobResponse[]>([]);
  const [appList, setAppList]     = useState<ApplicationResponse[]>([]);
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [jobStats, setJobStats]   = useState<Record<string, number>>({});
  const [appFunnel, setAppFunnel] = useState<Record<string, number>>({});
  const [open, setOpen]           = useState(true);

  const load = () => {
    jobs.list().then(setJobList).catch(console.error);
    applications.list().then(setAppList).catch(console.error);
    jobs.stats().then((s) => setJobStats(s.by_status)).catch(console.error);
    applications.analytics().then((a) => setAppFunnel(a.funnel)).catch(console.error);
    agents.runs().then(setAgentRuns).catch(console.error);
  };

  useEffect(() => { load(); }, []);

  const refreshJobs = () => {
    jobs.list().then(setJobList).catch(console.error);
    jobs.stats().then((s) => setJobStats(s.by_status)).catch(console.error);
  };
  const refreshApps = () => {
    applications.list().then(setAppList).catch(console.error);
    applications.analytics().then((a) => setAppFunnel(a.funnel)).catch(console.error);
  };

  return (
    <div className="min-h-screen flex bg-bg">
      {/* Sidebar */}
      <aside className={`${open ? "w-60" : "w-[72px]"} bg-gradient-to-b from-[#0a0e16] to-[#080c14] border-r border-border flex flex-col shrink-0 transition-all duration-300`}>
        {/* Logo */}
        <div className="h-16 flex items-center gap-3 px-5">
          <div className="w-9 h-9 rounded-xl bg-primary/20 flex items-center justify-center shrink-0">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-[18px] h-[18px] text-primary">
              <path d="M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
            </svg>
          </div>
          {open && <span className="font-bold text-lg gradient-text tracking-tight">JobPilot</span>}
        </div>

        <nav className="flex-1 py-6 px-3 space-y-1">
          {NAV.map((item) => (
            <button key={item.id} onClick={() => setTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all cursor-pointer ${
                tab === item.id
                  ? "bg-primary/15 text-primary ring-1 ring-primary/20"
                  : "text-muted-fg hover:bg-muted hover:text-fg"
              }`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-[18px] h-[18px] shrink-0">
                <path d={item.d} />
              </svg>
              {open && <span>{item.label}</span>}
              {/* Badge: show pending jobs count on Jobs tab */}
              {open && item.id === "jobs" && jobList.filter(j => j.status === "discovered").length > 0 && (
                <span className="ml-auto text-[10px] font-bold bg-warning/20 text-warning px-1.5 py-0.5 rounded-full">
                  {jobList.filter(j => j.status === "discovered").length}
                </span>
              )}
              {open && item.id === "applications" && appList.filter(a => a.status === "resume_ready").length > 0 && (
                <span className="ml-auto text-[10px] font-bold bg-success/20 text-success px-1.5 py-0.5 rounded-full">
                  {appList.filter(a => a.status === "resume_ready").length}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* User footer */}
        <div className="border-t border-border p-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary/30 to-accent/20 flex items-center justify-center shrink-0 text-xs font-bold text-primary ring-1 ring-primary/20">
              {user?.name?.charAt(0).toUpperCase()}
            </div>
            {open && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate text-fg">{user?.name}</p>
                <p className="text-[11px] text-muted-fg truncate">{user?.email}</p>
              </div>
            )}
            <button onClick={logout} title="Sign out"
              className="text-muted-fg hover:text-danger transition-colors cursor-pointer shrink-0">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
              </svg>
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        {/* Topbar */}
        <header className="h-14 bg-bg/75 backdrop-blur-xl border-b border-border flex items-center justify-between px-6 sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <button onClick={() => setOpen(!open)} className="text-muted-fg hover:text-fg cursor-pointer">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                <path d="M3 12h18M3 6h18M3 18h18" />
              </svg>
            </button>
            <h1 className="text-base font-semibold capitalize text-fg">
              {tab === "agents" ? "AI Agents" : tab}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-fg bg-muted border border-border px-3 py-1 rounded-full">
              {jobList.length} jobs · {appList.length} applications
            </span>
          </div>
        </header>

        {/* Content */}
        <div className="p-6 animate-fade-in" key={tab}>
          {tab === "overview"     && <OverviewView jobs={jobList} apps={appList} jobStats={jobStats} appFunnel={appFunnel} agentRuns={agentRuns} onNavigate={setTab} />}
          {tab === "jobs"         && <JobsView jobs={jobList} onRefresh={refreshJobs} />}
          {tab === "applications" && <ApplicationsView apps={appList} jobs={jobList} onRefresh={refreshApps} />}
          {tab === "resume"       && <ResumeView />}
          {tab === "agents"       && <AgentsView runs={agentRuns} onRefresh={load} />}
        </div>
      </main>
    </div>
  );
}
