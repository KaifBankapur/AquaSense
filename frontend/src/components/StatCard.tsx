import type { LucideIcon } from "lucide-react";
import {
  AlertTriangle,
  Binoculars,
  Bug,
  CalendarDays,
  Droplets,
  GitBranch,
  MapPin,
  Percent,
  Scale,
  Sparkles,
  Users,
  Waves,
} from "lucide-react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const ICONS: Record<string, LucideIcon> = {
  droplets: Droplets,
  water: Waves,
  "alert-triangle": AlertTriangle,
  percent: Percent,
  activity: Binoculars,
  "map-pin": MapPin,
  users: Users,
  calendar: CalendarDays,
  bug: Bug,
  pipeline: GitBranch,
  scale: Scale,
  sparkles: Sparkles,
};

export function StatCard({
  label,
  value,
  unit,
  icon,
  hint,
  accent = "cyan",
  className,
}: {
  label: string;
  value: string;
  unit?: string;
  icon?: string;
  hint?: string;
  accent?: "cyan" | "red" | "amber" | "green" | "blue";
  className?: string;
}) {
  const Icon = (icon && ICONS[icon]) || Droplets;
  const accentClasses: Record<string, string> = {
    cyan: "bg-cyan-500/12 text-cyan-600 dark:text-cyan-300",
    red: "bg-red-500/12 text-red-600 dark:text-red-400",
    amber: "bg-amber-500/12 text-amber-600 dark:text-amber-400",
    green: "bg-emerald-500/12 text-emerald-600 dark:text-emerald-400",
    blue: "bg-sky-500/12 text-sky-600 dark:text-sky-400",
  };
  return (
    <Card className={cn("card-hover p-5", className)}>
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
          <p className="mt-2 truncate text-2xl font-bold tabular-nums">
            {value}
            {unit ? <span className="ml-1 text-sm font-medium text-muted-foreground">{unit}</span> : null}
          </p>
          {hint ? <p className="mt-1 truncate text-xs text-muted-foreground">{hint}</p> : null}
        </div>
        <div className={cn("rounded-lg p-2.5", accentClasses[accent])}>
          <Icon className="size-5" />
        </div>
      </div>
    </Card>
  );
}