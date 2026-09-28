import { type CSSProperties, type ReactNode } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Droplets,
  Gauge,
  TrendingUp,
  Waves,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router-dom";

import { AnimatedNumber } from "@/components/ui/animated-number";
import { Button } from "@/components/ui/button";
import FlipText from "@/components/ui/flip-text";
import MorphText from "@/components/ui/morph-text";
import StaggerText from "@/components/ui/stagger-text";
import { cn } from "@/lib/utils";
import { fmtLiters, fmtPct } from "@/lib/format";
import type { DashboardSummary, WastageResponse } from "@/types/analytics";

const MORPH_WORDS = ["wastage", "undetected leaks", "demand spikes", "anomalies"];

const GRID_BG: CSSProperties = {
  backgroundImage:
    "linear-gradient(to right, hsl(var(--border) / 0.4) 1px, transparent 1px)," +
    "linear-gradient(to bottom, hsl(var(--border) / 0.4) 1px, transparent 1px)",
  backgroundSize: "44px 44px",
  WebkitMaskImage: "radial-gradient(ellipse 80% 65% at 30% 5%, black 5%, transparent 70%)",
  maskImage: "radial-gradient(ellipse 80% 65% at 30% 5%, black 5%, transparent 70%)",
  opacity: 0.4,
};

const RING_INNER = [
  { Icon: Droplets, className: "text-cyan-400" },
  { Icon: AlertTriangle, className: "text-amber-400" },
  { Icon: Gauge, className: "text-sky-400" },
  { Icon: TrendingUp, className: "text-emerald-400" },
];

const RING_OUTER = [
  { Icon: Activity, className: "text-rose-400" },
  { Icon: Waves, className: "text-teal-400" },
];

interface HeroProps {
  summary: DashboardSummary | null;
  wastage: WastageResponse | null;
}

/**
 * Dashboard hero — designed after 21st.dev "Hero Section 06"
 * (orbiting circles, glow gradients, live badge) with Vengeance UI
 * text animations (Stagger / Flip / Morph) and live analytics chips.
 */
export function Hero({ summary, wastage }: HeroProps) {
  const updated = summary?.generated_at?.replace("T", " ") ?? null;

  return (
    <section className="relative mb-8 overflow-hidden rounded-3xl border border-border bg-gradient-to-b from-card/80 via-background to-card/40 px-6 pb-10 pt-10 sm:px-10 lg:px-12">
      {/* ambient glows */}
      <div
        aria-hidden
        className="pointer-events-none absolute -left-24 -top-24 h-80 w-80 rounded-full bg-cyan-500/15 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -right-20 top-1/3 h-72 w-72 rounded-full bg-sky-500/10 blur-3xl"
      />
      {/* grid overlay */}
      <div aria-hidden className="pointer-events-none absolute inset-0" style={GRID_BG} />

      <div className="relative z-10 grid gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div>
          {/* live badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3.5 py-1.5 text-xs font-semibold text-primary">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-400" />
            </span>
            Live analytics{updated ? ` · updated ${updated}` : ""}
          </div>

          {/* headline — Vengeance UI Stagger Text */}
          <h1 className="text-gradient mt-6 text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl xl:text-[3.5rem]">
            <StaggerText divideBy="word" delay={0.15}>
              See where every drop goes.
            </StaggerText>
          </h1>

          {/* subtitle — Vengeance UI Flip Text (one-shot) */}
          <div className="mt-4 max-w-xl text-base text-muted-foreground sm:text-lg">
            <FlipText loop={false} duration={2.6} delay={0.5}>
              Big-data water analytics for Hubballi & Dharwad — every KPI computed by PySpark
              from 350,400 hourly records.
            </FlipText>
          </div>

          {/* rotating focus word — Vengeance UI Morph Text */}
          <div className="mt-7">
            <MorphText
              words={MORPH_WORDS}
              interval={3400}
              fontSize="clamp(1.9rem, 4vw, 3rem)"
              fontFamily={'"Space Grotesk", "Inter", sans-serif'}
              subtext="real-time detection · 10 service areas"
              className="items-start"
            />
          </div>

          {/* CTAs */}
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to="/areas">
              <Button className="rounded-full px-6">
                <ArrowRight className="size-4" /> Explore analytics
              </Button>
            </Link>
            <Link to="/assistant">
              <Button variant="outline" className="rounded-full px-6">
                <Waves className="size-4" /> Ask AquaAI
              </Button>
            </Link>
          </div>

          {/* live stat chips */}
          <div className="mt-10 grid max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
            <Chip label="Consumed">{summary ? fmtLiters(summary.total_consumed_liters) : "—"}</Chip>
            <Chip label="Wastage rate">{summary ? fmtPct(summary.wastage_rate_pct) : "—"}</Chip>
            <Chip label="Active areas">
              {summary ? <AnimatedNumber value={summary.active_areas} /> : "—"}
            </Chip>
            <Chip label="Leak events">
              {wastage ? <AnimatedNumber value={wastage.leak_event_count} /> : "—"}
            </Chip>
          </div>
        </div>

        {/* orbiting water core — hidden below lg */}
        <div className="hidden lg:block">
          <WaterCore />
        </div>
      </div>
    </section>
  );
}

function Chip({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-border/60 bg-card/70 px-4 py-3 backdrop-blur-sm">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        {label}
      </p>
      <div className="mt-1 text-xl font-bold tabular-nums">{children}</div>
    </div>
  );
}

function WaterCore() {
  return (
    <div className="relative mx-auto h-[420px] w-[420px]">
      <div className="absolute inset-0">
        <OrbitRing radius={168} duration={26} items={RING_INNER} />
        <OrbitRing radius={94} duration={19} reverse items={RING_OUTER} />
      </div>

      {/* nucleus */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        <div className="relative flex h-28 w-28 items-center justify-center">
          <div className="absolute inset-2 rounded-full bg-cyan-500/40 blur-2xl" />
          <div className="absolute inset-0 animate-[aqua-breathe_3s_ease-in-out_infinite] rounded-full border border-cyan-400/50" />
          <div className="relative flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-cyan-400 via-sky-500 to-teal-600 shadow-[0_0_80px_rgba(6,182,212,0.55)]">
            <Waves className="size-11 text-white" />
          </div>
        </div>
      </div>

      <p className="absolute inset-x-0 bottom-0 text-center text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
        Big-data pipeline · Spark 4.2.0
      </p>
    </div>
  );
}

function OrbitRing({
  radius,
  duration,
  reverse = false,
  items,
}: {
  radius: number;
  duration: number;
  reverse?: boolean;
  items: { Icon: LucideIcon; className: string }[];
}) {
  const size = radius * 2;
  return (
    <>
      {/* dashed orbit path */}
      <svg
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
        width={size}
        height={size}
        viewBox="0 0 1 1"
        style={{ overflow: "visible" }}
      >
        <circle
          cx={0.5}
          cy={0.5}
          r={0.5}
          fill="none"
          stroke="hsl(var(--border))"
          strokeOpacity={0.5}
          strokeDasharray="3 5"
        />
      </svg>
      {items.map(({ Icon, className }, i) => (
        <div key={i} className="absolute left-1/2 top-1/2">
          <div
            className="will-change-transform"
            style={{
              "--orbit-radius": `${radius}px`,
              animation: `aqua-orbit ${duration}s linear infinite`,
              animationDirection: reverse ? "reverse" : "normal",
              animationDelay: `${(duration / items.length) * -i}s`,
            } as CSSProperties}
          >
            <div
              className={cn(
                "flex h-12 w-12 -translate-x-1/2 -translate-y-1/2 items-center justify-center",
                "rounded-2xl border border-border/80 bg-card/80 shadow-lg shadow-black/20 backdrop-blur-sm",
              )}
            >
              <Icon className={cn("size-5", className)} />
            </div>
          </div>
        </div>
      ))}
    </>
  );
}