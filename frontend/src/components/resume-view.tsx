"use client";

import { useState, useEffect } from "react";
import { resumes, type ResumeResponse } from "@/lib/api";

export default function ResumeView() {
  const [resume, setResume] = useState<ResumeResponse | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState({
    name: "", title: "", summary: "", email: "", phone: "", location: "",
    linkedin: "", github: "", portfolio: "", skills: "",
    experience: JSON.stringify([{ company: "", role: "", start_date: "", end_date: "", bullets: [""] }], null, 2),
    education: JSON.stringify([{ institution: "", degree: "", year: "" }], null, 2),
    projects: JSON.stringify([{ name: "", description: "", tech_stack: [], url: "" }], null, 2),
  });

  useEffect(() => {
    resumes.active().then((r) => { setResume(r); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
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
    } catch (err) { console.error(err); }
    finally { setSaving(false); }
  };

  const inputCls = "w-full px-3.5 py-2.5 rounded-xl bg-muted border border-border text-sm text-fg placeholder:text-muted-fg/50 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all";

  if (loading) return <p className="text-muted-fg text-sm p-6">Loading resume...</p>;

  const rd = resume?.resume_data as Record<string, unknown> | null;

  return (
    <div className="space-y-5 max-w-[900px]">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-fg">{resume ? "Your active master resume" : "No resume uploaded yet"}</p>
        <button onClick={() => setShowForm(!showForm)}
          className="text-sm px-5 py-2 rounded-xl bg-gradient-to-r from-primary to-[#6c5ce7] text-white font-medium hover:shadow-lg hover:shadow-primary/25 transition-all cursor-pointer">
          {resume ? "Update Resume" : "Create Resume"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSave} className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 space-y-4 animate-fade-in">
          <h3 className="font-semibold text-sm text-fg">Resume Details</h3>
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

      {resume && rd && !showForm && (
        <div className="bg-card border border-border rounded-2xl p-6 shadow-lg shadow-black/20 animate-fade-in space-y-5">
          <div>
            <h2 className="text-xl font-bold text-fg">{rd.name as string}</h2>
            <p className="text-sm text-accent font-medium mt-0.5">{rd.title as string}</p>
            {rd.summary && <p className="text-sm text-muted-fg mt-3 leading-relaxed">{rd.summary as string}</p>}
          </div>

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
                <div key={i} className="mb-4 pl-4 border-l-2 border-primary/30">
                  <p className="text-sm font-semibold text-fg">{exp.role as string} <span className="font-normal text-muted-fg">at</span> {exp.company as string}</p>
                  <p className="text-xs text-muted-fg mt-0.5">{exp.start_date as string} - {exp.end_date as string}</p>
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
                <div key={i} className="mb-2 pl-4 border-l-2 border-accent/30">
                  <p className="text-sm font-medium text-fg">{edu.degree as string}</p>
                  <p className="text-xs text-muted-fg">{edu.institution as string} · {edu.year as string}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
