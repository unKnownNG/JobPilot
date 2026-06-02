"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";

export default function AuthPage() {
  const { setup } = useAuth();
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setError("");
    setLoading(true);
    try {
      await setup(name.trim());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute -top-40 -left-20 w-[500px] h-[500px] rounded-full bg-primary/8 blur-[120px]" />
      <div className="absolute -bottom-40 -right-20 w-[400px] h-[400px] rounded-full bg-accent/8 blur-[100px]" />

      <div className="w-full max-w-md px-6 animate-fade-in relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold gradient-text mb-2">JobPilot</h1>
          <p className="text-muted-fg text-sm">AI-powered job search &amp; application automation</p>
        </div>

        {/* Card */}
        <div className="bg-card/80 backdrop-blur-xl border border-border rounded-2xl p-8 shadow-2xl shadow-black/40">
          <h2 className="text-xl font-semibold mb-2 text-center text-fg">
            Welcome aboard ✈
          </h2>
          <p className="text-sm text-muted-fg text-center mb-6">
            Enter your name to get started. No account needed — everything runs locally on your machine.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-muted-fg mb-1.5">Your Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                minLength={2}
                placeholder="e.g. Mohammed"
                autoFocus
                className="w-full px-4 py-2.5 rounded-xl bg-muted border border-border text-fg placeholder:text-muted-fg/50 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
              />
            </div>

            {error && (
              <p className="text-danger text-sm bg-danger/10 border border-danger/20 rounded-xl px-4 py-2.5">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-primary to-[#6c5ce7] text-white font-semibold hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0 transition-all cursor-pointer"
            >
              {loading ? "Setting up..." : "Get Started"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
