"use client";

import { useState, useEffect, useRef } from "react";
import { resumes, type ResumeResponse } from "@/lib/api";

export default function ResumeView() {
  const [resume, setResume] = useState<ResumeResponse | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [form, setForm] = useState({
    name: "", title: "", summary: "", email: "", phone: "", location: "",
    linkedin: "", github: "", portfolio: "", skills: "",
    experience: JSON.stringify([{ company: "", role: "", start_date: "", end_date: "", bullets: [""] }], null, 2),
    education: JSON.stringify([{ institution: "", degree: "", year: "" }], null, 2),
    projects: JSON.stringify([{ name: "", description: "", tech_stack: [], url: "" }], null, 2),
  });

  useEffect(() => {
    resumes.active()
      .then((r) => { setResume(r); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const handleFileUpload = async (file: File) => {
    if (!file) return;
    setError("");
    setUploading(true);
    setUploadProgress("Extracting text from your resume...");

    try {
      await new Promise((r) => setTimeout(r, 600));
      setUploadProgress("Sending to AI for parsing (this takes ~20 seconds)...");
      const r = await resumes.upload(file);
      setResume(r);
      setUploadProgress("");
      setUploading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setUploadProgress("");
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileUpload(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const data = {
        name: form.name, title: form.title, summary: form.summary,
        email: form.email, phone: form.phone, location: form.location,
        linkedin: form.linkedin, github: form.github, portfolio: form.portfolio,
        skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
        experience: JSON.parse(form.experience),
        education: JSON.parse(form.education),
        projects: JSON.parse(form.projects),
      };
      const r = await resumes.create(data);
      setResume(r);
      setShowForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally { setSaving(false); }
  };

  const inputCls = "w-full px-3.5 py-2.5 rounded-xl bg-muted border border-border text-sm text-fg placeholder:text-muted-fg/50 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all";

  if (loading) return <p className="text-muted-fg text-sm p-6">Loading resume...</p>;

  const rd = resume?.resume_data as Record<string, unknown> | null;

  return (
    <div className="space-y-5 max-w-[900px]">

      {/* Header */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-fg">{resume ? "Your active master resume" : "No resume uploaded yet"}</p>
        <div className="flex gap-2">
          {resume && (
            <button onClick={() => setShowForm(!showForm)}
              className="text-sm px-4 py-2 rounded-xl bg-muted border border-border text-muted-fg hover:text-fg transition cursor-pointer">
              {showForm ? "Cancel" : "Edit Manually"}
            </button>
          )}
          <button onClick={() => fileInputRef.current?.click()}
            className="text-sm px-5 py-2 rounded-xl bg-gradient-to-r from-primary to-[#6c5ce7] text-white font-medium hover:shadow-lg hover:shadow-primary/25 transition-all cursor-pointer flex items-center gap-2">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
              <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
            </svg>
            {resume ? "Re-upload Resume" : "Upload Resume"}
          </button>
          <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt,.md"
            onChange={handleFileChange} className="hidden" />
        </div>
      </div>

      {/* Upload drop zone (shown when no resume yet) */}
      {!resume && !uploading && (
        <div
          onDrop={handleDrop}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
            dragOver ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/30"
          }`}>
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-7 h-7 text-primary">
                <path d="M9 12h6m-3-3v6M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-fg">Drop your resume here or click to browse</p>
              <p className="text-xs text-muted-fg mt-1">Supports PDF, DOCX, TXT · Max 10MB</p>
            </div>
            <div className="flex gap-2 mt-2">
              {["PDF", "DOCX", "TXT"].map(t => (
                <span key={t} className="text-[11px] font-medium px-2.5 py-1 rounded-full bg-muted text-muted-fg border border-border">{t}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Upload progress */}
      {uploading && (
        <div className="bg-primary/8 border border-primary/20 rounded-2xl p-6 flex items-center gap-4 animate-fade-in">
          <div className="w-10 h-10 rounded-xl bg-primary/15 flex items-center justify-center shrink-0">
            <svg className="w-5 h-5 text-primary animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-fg">Processing your resume...</p>
            <p className="text-xs text-muted-fg mt-0.5">{uploadProgress}</p>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-danger/10 border border-danger/20 rounded-xl p-3 text-sm text-danger animate-fade-in">
          ⚠️ {error}
        </div>
      )}

      {/* Manual Edit Form */}
      {showForm && !uploading && (
        <form onSubmit={handleSave} className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 space-y-4 animate-fade-in">
          <h3 className="font-semibold text-sm text-fg">Edit Resume Manually</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {(["name","title","email","phone","location","linkedin","github","portfolio"] as const).map((f) => (
              <input key={f} placeholder={f.charAt(0).toUpperCase() + f.slice(1)} value={form[f]}
                onChange={(e) => setForm({ ...form, [f]: e.target.value })}
                required={f === "name" || f === "title"} className={inputCls} />
            ))}
          </div>
          <textarea placeholder="Professional Summary" value={form.summary}
            onChange={(e) => setForm({ ...form, summary: e.target.value })} rows={2} className={`${inputCls} resize-none`} />
          <input placeholder="Skills (comma-separated: Python, React, SQL...)" value={form.skills}
            onChange={(e) => setForm({ ...form, skills: e.target.value })} className={inputCls} />
          <div>
            <label className="text-xs text-muted-fg font-medium mb-1 block">Experience (JSON)</label>
            <textarea value={form.experience} onChange={(e) => setForm({ ...form, experience: e.target.value })}
              rows={5} className={`${inputCls} font-mono text-xs resize-none`} />
          </div>
          <div>
            <label className="text-xs text-muted-fg font-medium mb-1 block">Education (JSON)</label>
            <textarea value={form.education} onChange={(e) => setForm({ ...form, education: e.target.value })}
              rows={3} className={`${inputCls} font-mono text-xs resize-none`} />
          </div>
          <div>
            <label className="text-xs text-muted-fg font-medium mb-1 block">Projects (JSON)</label>
            <textarea value={form.projects} onChange={(e) => setForm({ ...form, projects: e.target.value })}
              rows={3} className={`${inputCls} font-mono text-xs resize-none`} />
          </div>
          <div className="flex gap-3 justify-end">
            <button type="button" onClick={() => setShowForm(false)}
              className="text-sm px-4 py-2 rounded-xl bg-muted text-muted-fg border border-border cursor-pointer hover:text-fg transition">Cancel</button>
            <button type="submit" disabled={saving}
              className="text-sm px-5 py-2 rounded-xl bg-gradient-to-r from-primary to-[#6c5ce7] text-white font-medium disabled:opacity-50 cursor-pointer transition">
              {saving ? "Saving..." : "Save Resume"}
            </button>
          </div>
        </form>
      )}

      {/* Resume display */}
      {resume && rd && !showForm && (
        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in space-y-6">

          {/* Header info */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-fg">{rd.name as string}</h2>
              <p className="text-sm text-accent font-medium mt-0.5">{rd.title as string}</p>
              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2">
                {rd.email && <span className="text-xs text-muted-fg">✉ {rd.email as string}</span>}
                {rd.phone && <span className="text-xs text-muted-fg">📱 {rd.phone as string}</span>}
                {rd.location && <span className="text-xs text-muted-fg">📍 {rd.location as string}</span>}
              </div>
              <div className="flex flex-wrap gap-x-4 mt-1">
                {rd.linkedin && <a href={rd.linkedin as string} target="_blank" rel="noopener" className="text-xs text-primary hover:underline">LinkedIn</a>}
                {rd.github && <a href={rd.github as string} target="_blank" rel="noopener" className="text-xs text-primary hover:underline">GitHub</a>}
                {rd.portfolio && <a href={rd.portfolio as string} target="_blank" rel="noopener" className="text-xs text-primary hover:underline">Portfolio</a>}
              </div>
            </div>
            <div className="text-right shrink-0">
              <span className="text-[11px] px-2.5 py-1 rounded-full bg-success/15 text-success font-medium">Active</span>
              <p className="text-[11px] text-muted-fg mt-1">
                {resume.created_at ? new Date(resume.created_at).toLocaleDateString() : ""}
              </p>
            </div>
          </div>

          {rd.summary && (
            <div>
              <h4 className="text-xs font-semibold text-muted-fg uppercase tracking-wider mb-2">Summary</h4>
              <p className="text-sm text-muted-fg leading-relaxed">{rd.summary as string}</p>
            </div>
          )}

          {Array.isArray(rd.skills) && rd.skills.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-muted-fg uppercase tracking-wider mb-3">Skills</h4>
              <div className="flex flex-wrap gap-2">
                {(rd.skills as string[]).map((s) => (
                  <span key={s} className="text-xs px-3 py-1 rounded-full bg-primary/15 text-primary font-medium">{s}</span>
                ))}
              </div>
            </div>
          )}

          {Array.isArray(rd.experience) && rd.experience.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-muted-fg uppercase tracking-wider mb-3">Experience</h4>
              {(rd.experience as Record<string, unknown>[]).map((exp, i) => (
                <div key={i} className="mb-5 pl-4 border-l-2 border-primary/30">
                  <p className="text-sm font-semibold text-fg">{exp.role as string} <span className="font-normal text-muted-fg">at</span> {exp.company as string}</p>
                  <p className="text-xs text-muted-fg mt-0.5">{exp.start_date as string} – {exp.end_date as string}{exp.location ? ` · ${exp.location}` : ""}</p>
                  {Array.isArray(exp.bullets) && (
                    <ul className="text-xs text-muted-fg mt-2 space-y-1 list-disc list-inside">
                      {(exp.bullets as string[]).map((b, j) => <li key={j}>{b}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}

          {Array.isArray(rd.education) && rd.education.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-muted-fg uppercase tracking-wider mb-3">Education</h4>
              {(rd.education as Record<string, unknown>[]).map((edu, i) => (
                <div key={i} className="mb-3 pl-4 border-l-2 border-accent/30">
                  <p className="text-sm font-medium text-fg">{edu.degree as string}</p>
                  <p className="text-xs text-muted-fg">{edu.institution as string}{edu.year ? ` · ${edu.year}` : ""}{edu.gpa ? ` · GPA: ${edu.gpa}` : ""}</p>
                </div>
              ))}
            </div>
          )}

          {Array.isArray(rd.projects) && rd.projects.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-muted-fg uppercase tracking-wider mb-3">Projects</h4>
              {(rd.projects as Record<string, unknown>[]).map((proj, i) => (
                <div key={i} className="mb-3 pl-4 border-l-2 border-warning/30">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-fg">{proj.name as string}</p>
                    {proj.url && <a href={proj.url as string} target="_blank" rel="noopener" className="text-xs text-primary hover:underline">↗ Link</a>}
                  </div>
                  {proj.description && <p className="text-xs text-muted-fg mt-0.5">{proj.description as string}</p>}
                  {Array.isArray(proj.tech_stack) && proj.tech_stack.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {(proj.tech_stack as string[]).map(t => (
                        <span key={t} className="text-[10px] px-2 py-0.5 rounded-full bg-warning/10 text-warning border border-warning/20">{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {Array.isArray(rd.certifications) && rd.certifications.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-muted-fg uppercase tracking-wider mb-2">Certifications</h4>
              <div className="flex flex-wrap gap-2">
                {(rd.certifications as string[]).map((c) => (
                  <span key={c} className="text-xs px-3 py-1 rounded-full bg-accent/10 text-accent border border-accent/20">{c}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
