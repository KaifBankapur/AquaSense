import { Activity, ArrowRight, CalendarClock, GitBranch, Timer } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Area, AreaChart, ResponsiveContainer } from "recharts";

import { ConsumptionTrendChart } from "@/charts/ConsumptionTrendChart";
import { HorizontalBars } from "@/charts/Bars";
import { WeekHourHeatmap } from "@/charts/Heatmap";
import { Hero } from "@/components/Hero";
import { StatCard } from "@/components/StatCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ErrorState, LoadingState } from "@/components/States";
import { useApi } from "@/hooks/useApi";
import { useAreas } from "@/hooks/useAreas";
import { api } from "@/lib/api";
import { fmtLiters, fmtNum, fmtPct, secondsToClock, shortLabel } from "@/lib/format";
import type { TrendPoint } from "@/types/analytics";

function Sparkline({ data, color = "#0891b2" }: { data: number[]; color?: string }) {
  const points = useMemo(() => data.map((v, i) => ({ i, v })), [data]);
  if (!points.length) return <div className="h-10" />;
  return (
    <div className="mt-3 h-10">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`spark-${color}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area dataKey="v" stroke={color} strokeWidth={1.5} fill={`url(#spark-${color})`} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

const SECTION_LABELS: Record<string, { title: string; desc: string }> = {
  total_consumption: { title: "Total Consumption", desc: "City-wide water consumed" },
  total_supplied: { title: "Total Supplied", desc: "Water dispatched to the grid" },
  total_wastage: { title: "Total Wastage", desc: "Supply minus consumption" },
  wastage_rate: { title: "Wastage Rate", desc: "Share of supply lost" },
  peak_consumption: { title: "Peak Consumption", desc: "Busiest single hour" },
  active_areas: { title: "Active Areas", desc: "Areas under monitoring" },
};

export function DashboardPage() {
  const summary = useApi(() => api.dashboardSummary(), []);
  const kpis = useApi(() => api.kpis(), []);
  const areas = useAreas();
  const wastage = useApi(() => api.wastage(), []);
  const peaks = useApi(() => api.peaks(), []);
  const anomalies = useApi(() => api.anomalies({ page_size: 5 }), []);
  const forecast = useApi(() => api.forecast(), []);
  const pipeline = useApi(() => api.pipeline(), []);

  const [granularity, setGranularity] = useState<"daily" | "monthly" | "hourly">("daily");
  const [areaId, setAreaId] = useState<string>("");
  const trend = useApi(
    () => api.trend({ granularity, area_id: areaId || undefined }),
    [granularity, areaId],
  );

  const trendPoints = (trend.data?.points ?? []) as TrendPoint[];

  return (
    <div>
      <Hero summary={summary.data} wastage={wastage.data} />

      {/* Section 1 — KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {kpis.data?.map((k) => (
          <Card key={k.key} className="card-hover p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{k.label}</p>
            <p className="mt-2 text-xl font-bold tabular-nums">
              {k.key === "wastage_rate" || k.key === "total_wastage" || k.key === "active_areas"
                ? k.key === "active_areas"
                  ? fmtNum(k.value)
                  : k.key === "wastage_rate"
                    ? fmtPct(k.value)
                    : fmtLiters(k.value)
                : fmtLiters(k.value)}
            </p>
            {k.sparkline && k.sparkline.length ? <Sparkline data={k.sparkline} /> : <div className="mt-3 h-10" />}
          </Card>
        ))}
        {!kpis.data && !kpis.loading && kpis.error ? (
          <div className="col-span-full">
            <ErrorState message={kpis.error} onRetry={kpis.reload} />
          </div>
        ) : null}
      </div>

      {/* Section 2 — consumption trend */}
      <div className="mt-6">
        <Tabs value={granularity} onValueChange={(v) => setGranularity(v as any)}>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <TabsList>
              <TabsTrigger value="daily">Daily</TabsTrigger>
              <TabsTrigger value="hourly">Hourly</TabsTrigger>
              <TabsTrigger value="monthly">Monthly</TabsTrigger>
            </TabsList>
            <Select
              className="w-56"
              value={areaId}
              onChange={(e) => setAreaId(e.target.value)}
              aria-label="Filter by area"
            >
              <option value="">All areas</option>
              {areas.areas.map((a) => (
                <option key={a.area_id} value={a.area_id}>
                  {a.area_name}
                </option>
              ))}
            </Select>
          </div>
          {trend.loading ? (
            <LoadingState label="Loading trend…" />
          ) : trend.error ? (
            <ErrorState message={trend.error} onRetry={trend.reload} />
          ) : (
            <ConsumptionTrendChart
              points={trendPoints}
              title={`Consumption over time — ${granularity}`}
              description={areaId ? `Filtered to one area` : "City-wide consumed vs wastage (litres)"}
            />
          )}
        </Tabs>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Section 3 — area consumption ranking */}
        <Card className="card-hover">
          <CardHeader className="flex-row items-start justify-between">
            <div>
              <CardTitle>Consumption by area</CardTitle>
              <CardDescription>Total litres consumed per service area</CardDescription>
            </div>
            <Link to="/areas" className="text-xs font-medium text-primary hover:underline">
              Explore areas →
            </Link>
          </CardHeader>
          <CardContent>
            {areas.loading ? (
              <LoadingState />
            ) : areas.error ? (
              <ErrorState message={areas.error} onRetry={areas.reload} />
            ) : (
              <HorizontalBars
                data={areas.areas.map((a) => ({ name: a.area_name, value: a.total_consumed }))}
                valueFormatter={(v) => fmtLiters(Number(v))}
              />
            )}
          </CardContent>
        </Card>

        {/* Section 4 — peak + heatmap */}
        <Card className="card-hover">
          <CardHeader className="flex-row items-start justify-between">
            <div>
              <CardTitle>Peak consumption</CardTitle>
              <CardDescription>Busiest hour across the grid</CardDescription>
            </div>
            <Link to="/peak" className="text-xs font-medium text-primary hover:underline">
              Full peak analysis →
            </Link>
          </CardHeader>
          <CardContent className="space-y-4">
            {peaks.data ? (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg bg-muted/60 p-3">
                    <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Peak hour</p>
                    <p className="mt-1 text-lg font-bold">{peaks.data.peak_hour.label}</p>
                    <p className="text-xs text-muted-foreground">{fmtLiters(peaks.data.peak_hour.liters)}</p>
                  </div>
                  <div className="rounded-lg bg-muted/60 p-3">
                    <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Top area</p>
                    <p className="mt-1 truncate text-lg font-bold">{peaks.data.peak_area.area_name}</p>
                    <p className="text-xs text-muted-foreground">{fmtLiters(peaks.data.peak_area.liters)}</p>
                  </div>
                </div>
                <WeekHourHeatmap cells={peaks.data.heatmap} />
              </>
            ) : peaks.loading ? (
              <LoadingState />
            ) : (
              <ErrorState message={peaks.error ?? "peaks unavailable"} onRetry={peaks.reload} />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Section 5 — wastage snapshot */}
        <Card className="card-hover xl:col-span-1">
          <CardHeader className="flex-row items-start justify-between">
            <div>
              <CardTitle>Wastage snapshot</CardTitle>
              <CardDescription>Supply lost across the network</CardDescription>
            </div>
            <Badge variant="warning">
              {wastage.data ? fmtPct(wastage.data.wastage_rate_pct) : "…"}
            </Badge>
          </CardHeader>
          <CardContent>
            {wastage.data ? (
              <div className="space-y-3">
                <div>
                  <p className="text-2xl font-bold">{fmtLiters(wastage.data.total_wastage_liters)}</p>
                  <p className="text-xs text-muted-foreground">
                    of {fmtLiters(wastage.data.total_supplied_liters)} supplied
                  </p>
                </div>
                <div className="space-y-2">
                  {wastage.data.by_area.slice(0, 4).map((a) => (
                    <div key={a.area_id} className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">{a.area_name}</span>
                      <span className="font-medium tabular-nums">
                        {fmtLiters(a.wastage_liters)} · {fmtPct(a.wastage_pct)}
                      </span>
                    </div>
                  ))}
                </div>
                <Link to="/wastage" className="inline-block text-xs font-medium text-primary hover:underline">
                  View wastage analytics →
                </Link>
              </div>
            ) : wastage.loading ? (
              <LoadingState />
            ) : (
              <ErrorState message={wastage.error ?? "wastage unavailable"} onRetry={wastage.reload} />
            )}
          </CardContent>
        </Card>

        {/* Section 6 — anomalies preview */}
        <Card className="card-hover xl:col-span-1">
          <CardHeader className="flex-row items-start justify-between">
            <div>
              <CardTitle>Anomaly watch</CardTitle>
              <CardDescription>Unusual consumption events detected</CardDescription>
            </div>
            <Badge variant="destructive">{anomalies.data ? fmtNum(anomalies.data.total_flagged) : "…"}</Badge>
          </CardHeader>
          <CardContent>
            {anomalies.data ? (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {Object.entries(anomalies.data.counts).map(([cls, n]) => (
                    <Badge key={cls} variant="secondary">
                      {cls}: {fmtNum(n)}
                    </Badge>
                  ))}
                </div>
                <div className="space-y-1.5">
                  {anomalies.data.events.slice(0, 3).map((e, i) => (
                    <div key={i} className="rounded-md bg-muted/50 px-2.5 py-1.5 text-xs">
                      <span className="font-medium">{e.area_name}</span> · {e.household_id} ·{" "}
                      <Badge variant={e.severity === "critical" ? "destructive" : e.severity === "high" ? "warning" : "info"}>
                        {e.anomaly_class}
                      </Badge>
                      <span className="float-right text-muted-foreground">+{fmtPct(e.deviation_pct, 0)}</span>
                    </div>
                  ))}
                </div>
                <Link to="/anomalies" className="inline-block text-xs font-medium text-primary hover:underline">
                  View all anomalies →
                </Link>
              </div>
            ) : anomalies.loading ? (
              <LoadingState />
            ) : (
              <ErrorState message={anomalies.error ?? "anomalies unavailable"} onRetry={anomalies.reload} />
            )}
          </CardContent>
        </Card>

        {/* Section 7 — forecast preview */}
        <Card className="card-hover xl:col-span-1">
          <CardHeader className="flex-row items-start justify-between">
            <div>
              <CardTitle>Demand forecast</CardTitle>
              <CardDescription>Next 7 days · model predictions</CardDescription>
            </div>
            <Badge variant="info">
              <CalendarClock className="mr-1 size-3" />
              forecast
            </Badge>
          </CardHeader>
          <CardContent>
            {forecast.data ? (
              <div className="space-y-2.5">
                <p className="text-xs text-muted-foreground">
                  Method: <span className="font-mono">{forecast.data.method}</span> · trained on{" "}
                  {fmtNum(forecast.data.trained_on_days)} days
                </p>
                {forecast.data.forecast_7d.points.map((p) => (
                  <div key={p.date} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{shortLabel(p.date)}</span>
                    <span className="font-medium tabular-nums">{fmtLiters(p.predicted)}</span>
                  </div>
                ))}
                <Link to="/forecast" className="inline-block text-xs font-medium text-primary hover:underline">
                  Full forecast →
                </Link>
              </div>
            ) : forecast.loading ? (
              <LoadingState />
            ) : (
              <ErrorState message={forecast.error ?? "forecast unavailable"} onRetry={forecast.reload} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Section 8 — pipeline status */}
      <Card className="mt-6 card-hover">
        <CardHeader className="flex-row items-start justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="size-4 text-primary" /> Spark pipeline status
            </CardTitle>
            <CardDescription>Last processing run through the big-data layer</CardDescription>
          </div>
          <Link to="/pipeline">
            <Button variant="outline" size="sm">
              Pipeline <ArrowRight className="size-3.5" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {pipeline.data ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg bg-muted/60 p-3">
                <p className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-muted-foreground">
                  <Timer className="size-3.5" /> Ran at
                </p>
                <p className="mt-1 text-sm font-semibold">{pipeline.data.ran_at?.replace("T", " ")}</p>
              </div>
              <div className="rounded-lg bg-muted/60 p-3">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Records processed</p>
                <p className="mt-1 text-sm font-semibold">{fmtNum(pipeline.data.processed_records)}</p>
              </div>
              <div className="rounded-lg bg-muted/60 p-3">
                <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Duration</p>
                <p className="mt-1 text-sm font-semibold">
                  {pipeline.data.total_seconds ? secondsToClock(pipeline.data.total_seconds) : "—"}
                </p>
              </div>
              <div className="rounded-lg bg-muted/60 p-3">
                <p className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-muted-foreground">
                  <Activity className="size-3.5" /> Spark
                </p>
                <p className="mt-1 text-sm font-semibold">
                  {pipeline.data.cluster?.version} · {pipeline.data.cluster?.master}
                </p>
              </div>
            </div>
          ) : pipeline.loading ? (
            <LoadingState />
          ) : (
            <ErrorState
              message={pipeline.error ?? "Pipeline metadata unavailable"}
              onRetry={pipeline.reload}
            />
          )}
        </CardContent>
      </Card>

      {/* Underlying store line — keeps the demo honest */}
      <p className="mt-4 text-center text-[11px] text-muted-foreground">
        {summary.data
          ? `${fmtNum(summary.data.record_count)} records · ${fmtNum(summary.data.active_areas)} areas · generated ${
              summary.data.generated_at?.replace("T", " ") ?? "—"
            }`
          : "Loading dataset metadata…"}
      </p>
    </div>
  );
}