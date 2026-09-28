import { memo, useState } from "react";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Bot,
  Bug,
  CalendarClock,
  Droplets,
  Menu,
  TrendingUp,
  Waves,
  X,
  type LucideIcon,
} from "lucide-react";
import { Link } from "react-router-dom";

import ElectricLogo from "@/components/ui/electric-logo";
import ScrollReveal from "@/components/ui/scroll-reveal";
import { cn } from "@/lib/utils";

/**
 * SaaS landing template (21st.dev "saa-s-template"), adapted for AquaSense:
 * - hand-rolled SVGs replaced with lucide-react icons
 * - 21st.dev CDN preview art replaced with a live AquaSense dashboard mockup
 *   built in Tailwind, so the page has zero external image dependencies
 * - placeholder marketing copy replaced with real AquaSense copy; every
 *   anchor resolves to an actual app route via react-router <Link>
 * - Poppins font scoped to this page (loaded from index.html), keyframes
 *   (fadeIn / slideDown) live in index.css — no global `*` font override
 */

const NAV_LINKS = [
  { label: "Live demo", to: "/dashboard" },
  { label: "Analytics", to: "/areas" },
  { label: "Documentation", to: "/about" },
];

const FEATURES: { icon: LucideIcon; title: string; body: string; to: string }[] = [
  {
    icon: Droplets,
    title: "Wastage detection",
    body: "Night-flow minimums and continuous-leak scoring surface the taps nobody is metering.",
    to: "/wastage",
  },
  {
    icon: Activity,
    title: "Peak analysis",
    body: "Hour-of-day and day-of-week profiles separate real demand from pressure transients.",
    to: "/peak",
  },
  {
    icon: Bug,
    title: "Anomaly detection",
    body: "Stateless z-score outliers flag impossible readings and sudden demand spikes automatically.",
    to: "/anomalies",
  },
  {
    icon: CalendarClock,
    title: "Demand forecasting",
    body: "Spark aggregates project the next seven days so supply can be scheduled ahead of demand.",
    to: "/forecast",
  },
];

const linkBase =
  "inline-flex h-10 items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40 focus-visible:ring-offset-2 focus-visible:ring-offset-black";

const ghostLink = `${linkBase} px-3 text-white hover:bg-gray-800/50`;
const solidLink = `${linkBase} bg-white px-4 text-black hover:bg-gray-100`;

/**
 * Brand mark — the droplet from /aqua-mark.svg traced as electric strands.
 * Tuned down from the component defaults because a 40px mark has no room for
 * arcs or cursor interaction, and the fine crackle would just read as blur.
 * The wrapper owns the size so it can't race the component's own
 * `width/height: 100%` rule.
 */
function BrandMark({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn("block size-9 shrink-0 overflow-hidden", className)}
    >
      <ElectricLogo
        src="/aqua-mark.svg"
        color="#e0f7ff"
        glowColor="#22d3ee"
        scale={0.58}
        glow={0.75}
        thickness={1.2}
        strands={3}
        bend={0.4}
        crackle={1}
        arcs={0}
        flicker={0.35}
        speed={1.6}
        interactive={false}
      />
    </span>
  );
}

// ── Navigation ─────────────────────────────────────────────────────────────
const Navigation = memo(function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const close = () => setMobileMenuOpen(false);

  return (
    <header className="fixed top-0 z-50 w-full border-b border-gray-800/50 bg-black/80 backdrop-blur-md">
      <nav className="mx-auto max-w-7xl px-6 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 text-xl font-semibold text-white">
            <BrandMark />
            AquaSense
          </Link>

          <div className="absolute left-1/2 top-1/2 hidden -translate-x-1/2 -translate-y-1/2 items-center justify-center gap-8 md:flex">
            {NAV_LINKS.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className="text-sm text-white/60 transition-colors hover:text-white"
              >
                {l.label}
              </Link>
            ))}
          </div>

          <div className="hidden items-center gap-4 md:flex">
            <Link to="/assistant" className={ghostLink}>
              <Bot className="size-4" />
              AI Assistant
            </Link>
            <Link to="/dashboard" className={solidLink}>
              Open dashboard
            </Link>
          </div>

          <button
            type="button"
            className="text-white md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </nav>

      {mobileMenuOpen && (
        <div className="animate-[slideDown_0.3s_ease-out] border-t border-gray-800/50 bg-black/95 backdrop-blur-md md:hidden">
          <div className="flex flex-col gap-4 px-6 py-4">
            {NAV_LINKS.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className="py-2 text-sm text-white/60 transition-colors hover:text-white"
                onClick={close}
              >
                {l.label}
              </Link>
            ))}
            <div className="flex flex-col gap-2 border-t border-gray-800/50 pt-4">
              <Link to="/assistant" className={`${ghostLink} w-full`} onClick={close}>
                <Bot className="size-4" />
                AI Assistant
              </Link>
              <Link to="/dashboard" className={`${solidLink} w-full`} onClick={close}>
                Open dashboard
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
});
Navigation.displayName = "Navigation";

// ── Dashboard preview mockup ───────────────────────────────────────────────
/** Values mirror the project's own sample aggregates so the mockup reads true. */
const KPIS = [
  { label: "Total consumed", value: "13.01M", unit: "L" },
  { label: "Wastage rate", value: "4.52", unit: "%" },
  { label: "Active areas", value: "10", unit: "" },
  { label: "Leak events", value: "397", unit: "" },
];

/** wastage-rate % per month, Sep → Aug; the flagged month is highlighted. */
const MONTHLY = [
  { m: "Sep", v: 3.1 },
  { m: "Oct", v: 3.6 },
  { m: "Nov", v: 3.4 },
  { m: "Dec", v: 4.0 },
  { m: "Jan", v: 3.7 },
  { m: "Feb", v: 4.4 },
  { m: "Mar", v: 4.1 },
  { m: "Apr", v: 5.2, hot: true },
  { m: "May", v: 4.6 },
  { m: "Jun", v: 4.3 },
  { m: "Jul", v: 3.9 },
  { m: "Aug", v: 3.5 },
];

const MINI_NAV = [
  { label: "Dashboard", icon: BarChart3, active: true },
  { label: "Areas", icon: Droplets },
  { label: "Peak", icon: TrendingUp },
  { label: "Forecast", icon: CalendarClock },
  { label: "Assistant", icon: Bot },
];

const DashboardPreview = memo(function DashboardPreview() {
  return (
    <div className="relative mx-auto w-full max-w-5xl">
      {/* signature glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-0 h-[380px] w-[88%] -translate-x-1/2 -translate-y-1/4 rounded-full bg-cyan-500/20 blur-[130px]"
      />

      <div className="relative overflow-hidden rounded-xl border border-gray-800/80 bg-[#0a0a0a] shadow-2xl shadow-black/80 ring-1 ring-white/5">
        {/* window chrome */}
        <div className="flex items-center gap-2 border-b border-gray-800/70 bg-white/[0.02] px-4 py-3">
          <span className="size-2.5 rounded-full bg-gray-700" />
          <span className="size-2.5 rounded-full bg-gray-700" />
          <span className="size-2.5 rounded-full bg-gray-700" />
          <div className="mx-auto rounded-md border border-gray-800/70 bg-black/60 px-3 py-1 text-[11px] text-gray-500">
            aquasense.app/dashboard
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-[168px_1fr]">
          {/* mini sidebar */}
          <aside className="hidden flex-col gap-1 border-r border-gray-800/70 p-3 sm:flex">
            <div className="mb-3 flex items-center gap-2 px-1.5 pt-1">
              <Waves className="size-4 text-cyan-400" />
              <span className="text-xs font-semibold text-white">AquaSense</span>
            </div>
            {MINI_NAV.map(({ label, icon: Icon, active }) => (
              <div
                key={label}
                className={`flex items-center gap-2 rounded-md px-2.5 py-1.5 text-xs ${
                  active ? "bg-white/10 text-white" : "text-gray-500"
                }`}
              >
                <Icon className="size-3.5" />
                {label}
              </div>
            ))}
            <div className="mt-auto rounded-lg border border-gray-800/70 bg-white/[0.02] p-2.5">
              <p className="flex items-center gap-1.5 text-[10px] font-semibold text-gray-300">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
                </span>
                Spark 4.2.0
              </p>
              <p className="mt-1 text-[10px] text-gray-500">350,400 rows · Parquet</p>
            </div>
          </aside>

          {/* content */}
          <div className="p-4 sm:p-5">
            <div className="mb-4 flex items-end justify-between">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-gray-500">
                  Smart water analytics
                </p>
                <p className="mt-1 text-sm font-semibold text-white">
                  See where every drop goes
                </p>
              </div>
              <span className="rounded-full border border-gray-700 bg-gray-800/50 px-2.5 py-1 text-[10px] text-gray-400">
                Last 12 months
              </span>
            </div>

            {/* KPI tiles */}
            <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
              {KPIS.map((k) => (
                <div
                  key={k.label}
                  className="rounded-lg border border-gray-800/70 bg-white/[0.02] p-3"
                >
                  <p className="truncate text-[10px] uppercase tracking-wide text-gray-500">
                    {k.label}
                  </p>
                  <p className="mt-1.5 text-lg font-semibold tabular-nums text-white">
                    {k.value}
                    {k.unit ? (
                      <span className="ml-0.5 text-xs font-medium text-gray-500">{k.unit}</span>
                    ) : null}
                  </p>
                </div>
              ))}
            </div>

            {/* bar chart */}
            <div className="mt-3 rounded-lg border border-gray-800/70 bg-white/[0.02] p-3.5">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-[11px] font-semibold text-gray-200">Wastage rate by month</p>
                <div className="flex items-center gap-3 text-[10px] text-gray-500">
                  <span className="flex items-center gap-1.5">
                    <span className="size-1.5 rounded-full bg-cyan-500" /> Normal
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="size-1.5 rounded-full bg-amber-400" /> Flagged
                  </span>
                </div>
              </div>
              <div className="flex h-28 items-end gap-1.5">
                {MONTHLY.map((d) => (
                  <div key={d.m} className="group flex flex-1 flex-col items-center gap-1.5">
                    <div
                      className={`w-full rounded-t-sm transition-all ${
                        d.hot
                          ? "bg-amber-400/90 shadow-[0_0_12px_rgba(251,191,36,0.45)]"
                          : "bg-cyan-500/70"
                      }`}
                      style={{ height: `${(d.v / 5.2) * 100}%` }}
                    />
                    <span className="text-[9px] text-gray-600">{d.m}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});
DashboardPreview.displayName = "DashboardPreview";

// ── Hero ───────────────────────────────────────────────────────────────────
const Hero = memo(function Hero() {
  return (
    <section
      className="relative flex flex-col items-center px-6 pb-20 pt-32 md:pt-40"
      style={{ animation: "fadeIn 0.6s ease-out" }}
    >
      <aside className="mb-8 inline-flex max-w-full flex-wrap items-center justify-center gap-2 rounded-full border border-gray-700 bg-gray-800/50 px-4 py-2 backdrop-blur-sm">
        <span className="whitespace-nowrap text-center text-xs text-gray-400">
          New — seven-day demand forecasting is live
        </span>
        <Link
          to="/forecast"
          className="flex items-center gap-1 whitespace-nowrap text-xs text-gray-400 transition-all hover:text-white active:scale-95"
        >
          See what&apos;s new
          <ArrowRight size={12} />
        </Link>
      </aside>

      <h1
        className="mb-6 max-w-3xl px-6 text-center text-4xl font-medium leading-tight md:text-5xl lg:text-6xl"
        style={{
          background: "linear-gradient(to bottom, #ffffff, #ffffff, rgba(255, 255, 255, 0.6))",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
          letterSpacing: "-0.05em",
        }}
      >
        Every drop of water, <br />
        accounted for
      </h1>

      <p className="mb-10 max-w-2xl px-6 text-center text-sm text-gray-400 md:text-base">
        Smart water analytics for Hubballi &amp; Dharwad — 350,400 hourly records aggregated by
        PySpark, <br className="hidden sm:block" />
        surfaced as a live dashboard instead of a spreadsheet.
      </p>

      <div className="relative z-10 mb-16 flex flex-wrap items-center justify-center gap-4">
        <Link
          to="/dashboard"
          aria-label="Go to the analytics dashboard"
          className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-gradient-to-b from-white via-white/95 to-white/60 px-8 text-base font-medium text-black transition-all hover:scale-105 active:scale-95"
        >
          Get started
        </Link>
        <Link
          to="/areas"
          aria-label="Explore the areas analytics"
          className="inline-flex h-12 items-center justify-center gap-2 rounded-lg border border-gray-700/80 px-8 text-base font-medium text-white/80 transition-all hover:scale-105 hover:text-white active:scale-95"
        >
          View analytics
        </Link>
      </div>

      <DashboardPreview />
    </section>
  );
});
Hero.displayName = "Hero";

// ── Statement (React Bits ScrollReveal) ────────────────────────────────────
const Statement = memo(function Statement() {
  return (
    <section className="mx-auto w-full max-w-4xl px-6 pb-8">
      <ScrollReveal
        baseOpacity={0.12}
        baseRotation={2}
        blurStrength={6}
        enableBlur
        textClassName="text-center text-2xl font-medium leading-snug tracking-tight text-gray-400 md:text-3xl"
      >
        From 350,400 hourly readings to one answer: where the water went, and what to do about it.
      </ScrollReveal>
    </section>
  );
});
Statement.displayName = "Statement";

// ── Feature strip ──────────────────────────────────────────────────────────
const Features = memo(function Features() {
  return (
    <section className="mx-auto w-full max-w-7xl px-6 pb-24">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map(({ icon: Icon, title, body, to }) => (
          <Link
            key={title}
            to={to}
            className="group rounded-lg border border-gray-800/70 bg-white/[0.02] p-5 transition-all hover:border-gray-700 hover:bg-white/[0.04]"
          >
            <div className="flex size-9 items-center justify-center rounded-lg border border-gray-800 bg-gray-900 text-cyan-400 transition-colors group-hover:border-cyan-500/40">
              <Icon className="size-4" />
            </div>
            <h3 className="mt-4 text-sm font-semibold text-white">{title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-gray-500">{body}</p>
            <span className="mt-4 inline-flex items-center gap-1 text-xs text-gray-400 transition-colors group-hover:text-white">
              Explore
              <ArrowRight size={12} className="transition-transform group-hover:translate-x-0.5" />
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
});
Features.displayName = "Features";

// ── Footer ─────────────────────────────────────────────────────────────────
const Footer = memo(function Footer() {
  return (
    <footer className="border-t border-gray-800/50">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Waves className="size-4 text-cyan-400" />
          AquaSense · Smart Water Consumption Analytics
        </div>
        <div className="flex items-center gap-6 text-sm text-gray-500">
          {NAV_LINKS.map((l) => (
            <Link key={l.to} to={l.to} className="transition-colors hover:text-white">
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </footer>
  );
});
Footer.displayName = "Footer";

// ── Main ───────────────────────────────────────────────────────────────────
export default function Component() {
  return (
    <main
      className="min-h-screen overflow-x-hidden bg-black text-white"
      style={{ fontFamily: "'Poppins', 'Inter', sans-serif" }}
    >
      <Navigation />
      <Hero />
      <Statement />
      <Features />
      <Footer />
    </main>
  );
}
