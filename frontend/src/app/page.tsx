"use client";

import { useAuth } from "@/lib/auth-context";
import AuthPage from "@/components/auth-page";
import Dashboard from "@/components/dashboard";

export default function Home() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-muted-foreground text-sm">Loading JobPilot...</p>
        </div>
      </div>
    );
  }

  if (!user) return <AuthPage />;
  return <Dashboard />;
}
