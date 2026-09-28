import { useMemo } from "react";

import { VerticalBars } from "@/charts/Bars";
import { WeekHourHeatmap } from "@/charts/Heatmap";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/States";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtLiters } from "@/lib/format";

export function PeakPage() {
  const peaks = useApi(() => api.peaks(), []);
  const d = peaks.data;

  const hourlyProfile = useMemo(() => {
    if (!d) return [];
    const hours = new Map<number, number>();
    for (const c of d.heatmap) hours.set(c.hour, (hours.get(c.hour) ?? 0) + c.liters);
    return Array.from(hours.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([hour, liters]) => ({ name: `${String(hour).padStart(2, "0")}:00`, value: liters }));
  }, [d]);

  return (
    <div>
      <PageHeader
        title="Peak Consumption Analysis"
        description="When is demand highest — by hour, day, week, month and area (real aggregates, no estimates)."
      />

      {peaks.loading ? (
        <LoadingState />
      ) : peaks.error || !d ? (
        <ErrorState message={peaks.error ?? "peaks unavailable"} onRetry={peaks.reload} />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <StatCard label="Peak hour" value={d.peak_hour.label} hint={fmtLiters(d.peak_hour.liters)} icon="activity" accent="cyan" />
            <StatCard label="Peak day" value={d.peak_day.day_name} hint={fmtLiters(d.peak_day.liters)} icon="calendar" accent="blue" />
            <StatCard label="Peak week" value={`Week ${d.peak_week.week}`} hint={`from ${d.peak_week.week_start}`} icon="calendar" accent="green" />
            <StatCard
              label="Peak month"
              value={`${d.peak_month.year}-${String(d.peak_month.month).padStart(2, "0")}`}
              hint={fmtLiters(d.peak_month.liters)}
              icon="calendar"
              accent="amber"
            />
            <StatCard label="Peak area" value={d.peak_area.area_name} hint={fmtLiters(d.peak_area.liters)} icon="map-pin" accent="red" />
          </div>

          <Card className="mt-6 card-hover">
            <CardHeader>
              <CardTitle>Consumption heatmap — day × hour</CardTitle>
              <CardDescription>
                Total litres for each day-of-week × hour cell across the whole dataset ({fmtLiters(d.total_liters)} total)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <WeekHourHeatmap cells={d.heatmap} />
            </CardContent>
          </Card>

          <Card className="mt-6 card-hover">
            <CardHeader>
              <CardTitle>Average hourly profile</CardTitle>
              <CardDescription>
                Sum of consumption per hour of day (aggregated over all days) — the classic demand curve
              </CardDescription>
            </CardHeader>
            <CardContent>
              <VerticalBars data={hourlyProfile} valueFormatter={(v) => fmtLiters(Number(v))} color="#0891b2" />
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}