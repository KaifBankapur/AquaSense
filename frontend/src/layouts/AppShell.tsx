import type { LucideIcon } from "lucide-react";
import {
  Activity,
  BarChart3,
  Bot,
  Bug,
  CalendarClock,
  Database,
  Droplets,
  FlaskConical,
  GitBranch,
  Info,
  LayoutTemplate,
  Map,
  Menu,
  Moon,
  Sun,
  Waves,
  X,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTheme } from "@/hooks/useTheme";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

const NAV: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: BarChart3, end: true },
  { to: "/", label: "Landing", icon: LayoutTemplate, end: true },
  { to: "/areas", label: "Areas", icon: Map },
  { to: "/wastage", label: "Wastage", icon: Droplets },
  { to: "/peak", label: "Peak Analysis", icon: Activity },
  { to: "/anomalies", label: "Anomalies", icon: Bug },
  { to: "/forecast", label: "Forecast", icon: CalendarClock },
  { to: "/data", label: "Data Explorer", icon: Database },
  { to: "/pipeline", label: "Pipeline", icon: GitBranch },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
  { to: "/about", label: "About", icon: Info },
];

function Brand() {
  return (
    <div className="flex items-center gap-2.5 px-1">
      <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-cyan-700 text-white shadow-lg shadow-cyan-500/25">
        <Waves className="size-5" />
      </div>
      <div className="leading-tight">
        <p className="text-sm font-bold tracking-tight">AquaSense</p>
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
          Smart Water Analytics
        </p>
      </div>
    </div>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { data: health } = useApi(() => api.health(), []);
  return (
    <div className="flex h-full flex-col gap-6 p-4">
      <Brand />
      <nav className="flex flex-1 flex-col gap-1">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/12 text-primary"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )
            }
          >
            <item.icon className="size-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="rounded-xl border bg-muted/40 p-3 text-xs leading-relaxed text-muted-foreground">
        <p className="mb-1 flex items-center gap-1.5 font-semibold text-foreground">
          <FlaskConical className="size-3.5" /> Data Layer
        </p>
        {health ? (
          <>
            <p>Spark {health.spark} · {health.dataset_present ? "dataset ready" : "dataset missing"}</p>
            <p>Service {health.service} v{health.version}</p>
          </>
        ) : (
          <p>Backend …</p>
        )}
      </div>
    </div>
  );
}

export function AppShell() {
  const [open, setOpen] = useState(false);
  const { theme, toggle } = useTheme();
  const location = useLocation();
  const active = NAV.find((n) =>
    n.end ? location.pathname === n.to : location.pathname.startsWith(n.to),
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 border-r bg-card lg:block">
        <SidebarContent />
      </aside>

      {/* Mobile drawer */}
      {open ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 bg-card shadow-xl">
            <button
              className="absolute right-3 top-3 rounded-md p-1 text-muted-foreground hover:bg-accent"
              onClick={() => setOpen(false)}
              aria-label="Close menu"
            >
              <X className="size-5" />
            </button>
            <SidebarContent onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="lg:pl-60">
        {/* Top bar */}
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur lg:px-6">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu className="size-5" />
          </Button>
          <h2 className="text-sm font-semibold">{active?.label ?? "AquaSense"}</h2>
          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggle}
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>
            <NavLink to="/assistant">
              <Button size="sm">
                <Bot className="size-4" /> AquaAI
              </Button>
            </NavLink>
          </div>
        </header>

        <main className="mx-auto max-w-[1400px] px-4 py-6 lg:px-6">
          <Outlet />
        </main>

        <footer className="border-t px-6 py-4 text-center text-xs text-muted-foreground">
          AquaSense · Smart Water Consumption Analytics · PySpark → Parquet → FastAPI → React
        </footer>
      </div>
    </div>
  );
}