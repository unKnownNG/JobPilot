"use client";

import { useState } from "react";
import { applications as appsApi, type ApplicationResponse, type JobResponse } from "@/lib/api";

interface Props {
  apps: ApplicationResponse[];
  jobs: JobResponse[];
  onRefresh: () => void;
}

const STATUS_STYLES: Record<string, string> = {
  queued:               "bg-muted text-muted-fg border border-border",
  resume_ready:         "bg-success/15 text-success",
  applying:             "bg-warning/15 text-warning",
  applied:              "bg-primary/15 text-primary",
  under_review:         "bg-accent/15 text-accent",
  interview_scheduled:  "bg-success/15 text-success",
  rejected:             "bg-danger/15 text-danger",
  offer_received:       "bg-warning/15 text-warning",
  accepted:             "bg-success/15 text-success",
  failed_to_apply:      "bg-danger/15 text-danger",
};

const ALL_STATUSES = Object.keys(STATUS_STYLES);

export default function ApplicationsView({ apps, jobs, onRefresh }: Props) {
  const [filter, setFilter]       = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editStatus, setEditStatus] = useState("");
  const [editNotes, setEditNotes]   = useState("");
  const [showHistory, setShowHistory] = useState<string | null>(null);

  const jobMap = Object.fromEntries(jobs.map(j => [j.id, j]));
  const filtered = filter ? apps.filter(a => a.status === filter) : apps;

  const saveEdit = async () => {
    if (!editingId) return;
    await appsApi.update(editingId, { status: editStatus, notes: editNotes });
    setEditingId(null);
    onRefresh();
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this application?")) return;
    await appsApi.delete(id);
    onRefresh();
  };

  const inputCls = "w-full px-3.5 py-2.5 rounded-xl bg-muted border border-border text-sm text-fg outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all";

  return (
    <div className="space-y-5 max-w-[1200px]">
      {/* Filter pills */}
      <div className="flex gap-2 flex-wrap">
        {["", "queued", "resume_ready", "applied", "under_review", "interview_scheduled", "rejected"].map(s => (
          <button key={s} onClick={() => setFilter(s)}
            className={`text-xs px-3.5 py-1.5 rounded-full font-medium capitalize cursor-pointer transition-all ${
              filter === s
                ? "bg-primary text-white shadow-md shadow-primary/25"
                : "bg-muted text-muted-fg border border-border hover:border-primary/30 hover:text-fg"
            }`}>
            {s ? s.replace(/_/g, " ") : `All (${apps.length})`}
          </button>
        ))}
      </div>

      {/* Stats mini row */}
      {apps.length > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {[
            { label: "Total",      val: apps.length,                                              col: "text-fg" },
            { label: "Queued",     val: apps.filter(a => a.status === "queued").length,           col: "text-muted-fg" },
            { label: "Ready",      val: apps.filter(a => a.status === "resume_ready").length,     col: "text-success" },
            { label: "Applied",    val: apps.filter(a => a.status === "applied").length,          col: "text-primary" },
            { label: "Interview",  val: apps.filter(a => a.status === "interview_scheduled").length, col: "text-success" },
            { label: "Rejected",   val: apps.filter(a => a.status === "rejected").length,         col: "text-danger" },
          ].map(({ label, val, col }) => (
            <div key={label} className="bg-card border border-border rounded-xl p-3 text-center shadow-sm">
              <p className={`text-xl font-bold ${col}`}>{val}</p>
              <p className="text-[11px] text-muted-fg">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* List */}
      {filtered.length === 0 ? (
        <div className="bg-card border border-border rounded-2xl p-16 text-center shadow-lg shadow-black/20">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-10 h-10 mx-auto mb-3 text-muted-fg/40">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>
          </svg>
          <p className="text-sm text-muted-fg">No applications yet. Approve jobs and run the Tailor Agent!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((app, i) => {
            const job = jobMap[app.job_posting_id];
            return (
              <div key={app.id}
                className="bg-card border border-border rounded-2xl shadow-md shadow-black/15 animate-fade-in hover:border-primary/25 transition-colors"
                style={{ animationDelay: `${i * 40}ms` }}>
                {editingId === app.id ? (
                  <div className="p-4 space-y-3">
                    <select value={editStatus} onChange={e => setEditStatus(e.target.value)} className={inputCls}>
                      {ALL_STATUSES.map(s => (
                        <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
                      ))}
                    </select>
                    <textarea value={editNotes} onChange={e => setEditNotes(e.target.value)}
                      placeholder="Add notes..." rows={2} className={`${inputCls} resize-none`} />
                    <div className="flex gap-2 justify-end">
                      <button onClick={() => setEditingId(null)}
                        className="text-xs px-3.5 py-1.5 rounded-xl bg-muted text-muted-fg border border-border cursor-pointer hover:text-fg transition">Cancel</button>
                      <button onClick={saveEdit}
                        className="text-xs px-3.5 py-1.5 rounded-xl bg-primary text-white cursor-pointer font-medium">Save</button>
                    </div>
                  </div>
                ) : (
                  <div className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        {/* Job info */}
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <p className="text-sm font-semibold text-fg">
                            {job ? job.title : `Application #${app.id.slice(0, 8)}`}
                          </p>
                          <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full capitalize ${STATUS_STYLES[app.status] || STATUS_STYLES.queued}`}>
                            {app.status.replace(/_/g, " ")}
                          </span>
                          {app.tailored_resume_id && (
                            <span className="text-[11px] bg-accent/10 text-accent px-2 py-0.5 rounded-full">tailored ✓</span>
                          )}
                        </div>
                        {job && (
                          <p className="text-xs text-muted-fg mb-1">
                            {job.company}{job.location ? ` · ${job.location}` : ""}{job.work_type ? ` · ${job.work_type}` : ""}
                          </p>
                        )}
                        {app.notes && (
                          <p className="text-xs text-muted-fg italic">Note: {app.notes}</p>
                        )}
                        <p className="text-[11px] text-muted-fg/60 mt-1">
                          Created {new Date(app.created_at).toLocaleDateString()}
                          {app.applied_at ? ` · Applied ${new Date(app.applied_at).toLocaleDateString()}` : ""}
                          {app.platform ? ` · via ${app.platform}` : ""}
                        </p>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 shrink-0">
                        {job && (
                          <a href={job.url} target="_blank" rel="noopener noreferrer"
                            className="text-xs px-3 py-1.5 rounded-lg bg-muted text-muted-fg border border-border hover:text-fg transition">
                            Open Job
                          </a>
                        )}
                        <button onClick={() => { setEditingId(app.id); setEditStatus(app.status); setEditNotes(app.notes || ""); }}
                          className="text-xs px-3 py-1.5 rounded-lg bg-muted text-muted-fg border border-border hover:text-fg transition cursor-pointer">Edit</button>
                        <button onClick={() => setShowHistory(showHistory === app.id + '_history' ? null : app.id + '_history')}
                          className="text-xs px-3 py-1.5 rounded-lg bg-muted text-muted-fg border border-border hover:text-fg transition cursor-pointer">History</button>
                        {app.screenshots && app.screenshots.length > 0 && (
                          <button onClick={() => setShowHistory(showHistory === app.id + '_images' ? null : app.id + '_images')}
                            className="text-xs px-3 py-1.5 rounded-lg bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition cursor-pointer flex items-center gap-1">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-3 h-3"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                            Screenshots
                          </button>
                        )}
                        <button onClick={() => handleDelete(app.id)}
                          className="text-xs px-2.5 py-1.5 rounded-lg bg-danger/10 text-danger border border-danger/20 hover:bg-danger hover:text-white transition cursor-pointer ml-1"
                          title="Delete Application">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-3.5 h-3.5"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6"/></svg>
                        </button>
                      </div>
                    </div>

                    {/* Status history */}
                    {showHistory === app.id + '_history' && app.status_history?.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border space-y-1.5">
                        {app.status_history.map((h, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-xs text-muted-fg">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary/50 shrink-0" />
                            <span className="capitalize font-medium text-fg">{String(h.status).replace(/_/g, " ")}</span>
                            <span>·</span>
                            <span>{h.note as string}</span>
                            <span className="ml-auto">{h.at ? new Date(h.at as string).toLocaleString() : ""}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Screenshots */}
                    {showHistory === app.id + '_images' && app.screenshots?.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-border">
                        <p className="text-xs text-muted-fg mb-3 font-medium">Screenshots captured by the Applier Agent:</p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {app.screenshots.map((path, idx) => {
                            const filename = path.split(/[\/\\]/).pop();
                            const url = `http://localhost:8000/storage/screenshots/${filename}`;
                            const titleParts = filename?.split('_') || [];
                            const stepName = titleParts.length > 2 ? titleParts.slice(1, -1).join(' ') : 'Screenshot';
                            
                            return (
                              <div key={idx} className="space-y-1.5">
                                <p className="text-[10px] text-muted-fg uppercase tracking-wider font-semibold">
                                  {stepName.replace(/_/g, ' ')}
                                </p>
                                <a href={url} target="_blank" rel="noopener noreferrer" className="block relative group overflow-hidden rounded-xl border border-border">
                                  <img src={url} alt="Applier screenshot" className="w-full aspect-video object-cover group-hover:scale-105 transition-transform duration-300" />
                                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                    <span className="text-white text-xs font-medium bg-black/50 px-3 py-1 rounded-full">View Full Size</span>
                                  </div>
                                </a>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
