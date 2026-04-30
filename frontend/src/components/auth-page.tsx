"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";

export default function AuthPage() {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isLogin) await login(email, password);
      else await register(email, name, password);
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
          <h2 className="text-xl font-semibold mb-6 text-center text-fg">
            {isLogin ? "Welcome back" : "Create account"}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm text-muted-fg mb-1.5">Name</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)}
                  required={!isLogin} placeholder="Your name"
                  className="w-full px-4 py-2.5 rounded-xl bg-muted border border-border text-fg placeholder:text-muted-fg/50 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all" />
              </div>
            )}
            <div>
              <label className="block text-sm text-muted-fg mb-1.5">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                required placeholder="you@example.com"
                className="w-full px-4 py-2.5 rounded-xl bg-muted border border-border text-fg placeholder:text-muted-fg/50 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all" />
            </div>
            <div>
              <label className="block text-sm text-muted-fg mb-1.5">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                required minLength={8} placeholder="Min 8 characters"
                className="w-full px-4 py-2.5 rounded-xl bg-muted border border-border text-fg placeholder:text-muted-fg/50 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all" />
            </div>

            {error && (
              <p className="text-danger text-sm bg-danger/10 border border-danger/20 rounded-xl px-4 py-2.5">{error}</p>
            )}

            <button type="submit" disabled={loading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-primary to-[#6c5ce7] text-white font-semibold hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0 transition-all cursor-pointer">
              {loading ? "Please wait..." : isLogin ? "Sign In" : "Create Account"}
            </button>
          </form>

          <p className="text-center text-sm text-muted-fg mt-6">
            {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
            <button onClick={() => { setIsLogin(!isLogin); setError(""); }}
              className="text-accent hover:text-primary hover:underline cursor-pointer font-medium transition-colors">
              {isLogin ? "Sign up" : "Sign in"}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
