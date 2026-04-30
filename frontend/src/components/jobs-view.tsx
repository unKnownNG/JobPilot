"use client";

import { useState } from "react";
import { jobs as jobsApi, type JobResponse } from "@/lib/api";

interface Props {
  jobs: JobResponse[];
  onRefresh: () => void;
}

export default function JobsView({ jobs: jobList, onRefresh }: Props) {
  const [showAdd, setShowAdd] = useState(false);
  const [filter, setFilter] = useState("");
  const [form, setForm] = useState({
    title: "", company: "", url: "", location: "",
    description: "", work_type: "remote", source: "manual",
  });
  const [loading, setLoading] = useState(false);

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

  const updateStatus = async (id: string, status: string) => {
    await jobsApi.updateStatus(id, status);
    onRefresh();
  };

  const inputCls = "w-full px-3.5 py-2.5 rounded-xl bg-muted border border-border text-sm text-fg placeholder:text-muted-fg/50 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all";

  return (
    <div className="space-y-5 max-w-[1200px]">
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
          <p className="text-sm text-muted-fg">No jobs found. Add one to get started!</p>
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
