"use client";

import { useState } from "react";
import { applications as appsApi, type ApplicationResponse } from "@/lib/api";

interface Props {
  apps: ApplicationResponse[];
  onRefresh: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  queued: "bg-muted text-muted-fg border border-border",
  resume_ready: "bg-accent/15 text-accent",
  applying: "bg-warning/15 text-warning",
  applied: "bg-primary/15 text-primary",
  under_review: "bg-accent/15 text-accent",
  interview_scheduled: "bg-success/15 text-success",
  rejected: "bg-danger/15 text-danger",
  offer_received: "bg-warning/15 text-warning",
  accepted: "bg-success/15 text-success",
  failed_to_apply: "bg-danger/15 text-danger",
};

export default function ApplicationsView({ apps, onRefresh }: Props) {
  const [filter, setFilter] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editStatus, setEditStatus] = useState("");
  const [editNotes, setEditNotes] = useState("");

  const filtered = filter ? apps.filter((a) => a.status === filter) : apps;

  const saveEdit = async () => {
    if (!editingId) return;
    await appsApi.update(editingId, { status: editStatus, notes: editNotes });
    setEditingId(null);
    onRefresh();
  };

  const inputCls = "w-full px-3.5 py-2.5 rounded-xl bg-muted border border-border text-sm text-fg outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all";

  return (
    <div className="space-y-5 max-w-[1200px]">
      <div className="flex gap-2 flex-wrap">
        {["", "queued", "applied", "under_review", "interview_scheduled", "rejected"].map((s) => (
          <button key={s} onClick={() => setFilter(s)}
            className={`text-xs px-3.5 py-1.5 rounded-full font-medium capitalize cursor-pointer transition-all ${
              filter === s
                ? "bg-primary text-white shadow-md shadow-primary/25"
                : "bg-muted text-muted-fg border border-border hover:border-primary/30 hover:text-fg"
            }`}>
            {s ? s.replace(/_/g, " ") : "All"}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="bg-card border border-border rounded-2xl p-16 text-center shadow-lg shadow-black/20">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-10 h-10 mx-auto mb-3 text-muted-fg/40">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4z" />
          </svg>
          <p className="text-sm text-muted-fg">No applications yet. Approve jobs to start applying!</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((app, i) => (
            <div key={app.id} className="bg-card border border-border rounded-2xl p-4 shadow-md shadow-black/15 animate-fade-in hover:border-primary/25 transition-colors"
              style={{ animationDelay: `${i * 40}ms` }}>
              {editingId === app.id ? (
                <div className="space-y-3">
                  <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)} className={inputCls}>
                    {Object.keys(STATUS_COLORS).map((s) => (
                      <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
                    ))}
                  </select>
                  <textarea value={editNotes} onChange={(e) => setEditNotes(e.target.value)}
                    placeholder="Add notes..." rows={2} className={`${inputCls} resize-none`} />
                  <div className="flex gap-2 justify-end">
                    <button onClick={() => setEditingId(null)}
                      className="text-xs px-3.5 py-1.5 rounded-xl bg-muted text-muted-fg border border-border cursor-pointer hover:text-fg transition">Cancel</button>
                    <button onClick={saveEdit}
                      className="text-xs px-3.5 py-1.5 rounded-xl bg-primary text-white cursor-pointer font-medium">Save</button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-fg">Application #{app.id.slice(0, 8)}</span>
                      <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full capitalize ${STATUS_COLORS[app.status] || STATUS_COLORS.queued}`}>
                        {app.status.replace(/_/g, " ")}
                      </span>
                    </div>
                    <p className="text-xs text-muted-fg">
                      {app.platform ? `${app.platform} · ` : ""}{new Date(app.created_at).toLocaleDateString()}
                      {app.notes ? ` · ${app.notes}` : ""}
                    </p>
                  </div>
                  <button onClick={() => { setEditingId(app.id); setEditStatus(app.status); setEditNotes(app.notes || ""); }}
                    className="text-xs px-3.5 py-1.5 rounded-xl bg-muted text-muted-fg border border-border hover:text-fg transition cursor-pointer shrink-0">Edit</button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
