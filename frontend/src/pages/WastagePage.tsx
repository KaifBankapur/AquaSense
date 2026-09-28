import { useMemo } from "react";

import { HorizontalBars } from "@/charts/Bars";
import { ConsumptionTrendChart } from "@/charts/ConsumptionTrendChart";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ErrorState, LoadingState } from "@/components/States";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtLiters, fmtPct } from "@/lib/format";

export function WastagePage() {
  const wastage = useApi(() => api.wastage(), []);
  const d = wastage.data;

  const dailyPoints = useMemo(() => {
    const w = wastage.data?.daily_wastage ?? [];
    return w.map((x) => ({ label: x.date, consumed: x.wastage_liters, wastage: 0 }));
  }, [wastage.data]);

  return (
    <div>
      <PageHeader
        title="Water Wastage"
        description="How much of the supplied water is lost, where it happens, and leak-like events."
      />

      {wastage.loading ? (
        <LoadingState />
      ) : wastage.error || !d ? (
        <ErrorState message={wastage.error ?? "wastage unavailable"} onRetry={wastage.reload} />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Total wastage" value={fmtLiters(d.total_wastage_liters)} icon="alert-triangle" accent="red" />
            <StatCard label="Wastage rate" value={fmtPct(d.wastage_rate_pct)} hint="of total supply" icon="percent" accent="amber" />
            <StatCard label="Avg hourly wastage" value={fmtPct(d.avg_wastage_pct)} hint="across all readings" icon="percent" accent="blue" />
            <StatCard label="Leak-like events" value={d.leak_event_count.toLocaleString()} hint={`flagged ≥ ${fmtPct(d.leak_threshold_pct, 0)} of supply`} icon="alert-triangle" accent="red" />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
            <Card className="xl:col-span-2 card-hover">
              <CardHeader>
                <CardTitle>Wastage by area</CardTitle>
                <CardDescription>Total litres lost per area and its share of that area's supply</CardDescription>
              </CardHeader>
              <CardContent>
                <HorizontalBars
                  data={d.by_area.map((a) => ({ name: a.area_name, value: a.wastage_liters }))}
                  valueFormatter={(v) => fmtLiters(Number(v))}
                />
              </CardContent>
            </Card>

            <Card className="card-hover">
              <CardHeader>
                <CardTitle>By building type</CardTitle>
                <CardDescription>Wastage aggregated by customer segment</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {d.by_building_type.map((b) => (
                    <div key={b.building_type}>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="capitalize">{b.building_type}</span>
                        <span className="font-medium tabular-nums">
                          {fmtLiters(b.wastage_liters)} · {fmtPct(b.wastage_pct)}
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-muted">
                        <div
                          className="h-2 rounded-full bg-gradient-to-r from-amber-400 to-red-500"
                          style={{ width: `${Math.min(100, b.wastage_pct * 8)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
            <TaskTrend points={dailyPoints} title="Daily wastage trend" />
            <Card className="card-hover">
              <CardHeader>
                <CardTitle>Monthly wastage</CardTitle>
                <CardDescription>Wastage litres and rate per month</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {d.monthly_wastage.map((m) => (
                    <div key={`${m.year}-${m.month}`} className="flex items-center justify-between text-sm">
                      <span className="font-medium">
                        {m.year}-{String(m.month).padStart(2, "0")}
                      </span>
                      <span className="tabular-nums text-muted-foreground">
                        {fmtLiters(m.wastage_liters)} ·{" "}
                        <Badge variant="secondary">{fmtPct(m.wastage_pct)}</Badge>
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Leak-like events</CardTitle>
              <CardDescription>
                {d.leak_event_count.toLocaleString()} readings where wastage exceeded {fmtPct(d.leak_threshold_pct, 0)} of supply
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Area</TableHead>
                    <TableHead>Household</TableHead>
                    <TableHead className="text-right">Supplied</TableHead>
                    <TableHead className="text-right">Consumed</TableHead>
                    <TableHead className="text-right">Wasted</TableHead>
                    <TableHead className="text-right">Wastage %</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {d.leak_events.slice(0, 12).map((e, i) => (
                    <TableRow key={i}>
                      <TableCell className="tabular-nums">{e.timestamp}</TableCell>
                      <TableCell className="font-medium">{e.area_name}</TableCell>
                      <TableCell className="font-mono text-xs">{e.household_id}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(e.supplied_water_liters)}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(e.consumed_water_liters)}</TableCell>
                      <TableCell className="text-right tabular-nums font-semibold text-red-500">
                        {fmtLiters(e.wastage_liters)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        <Badge variant="destructive">{fmtPct(e.wastage_percent)}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function TaskTrend({ points, title }: { points: { label: string; consumed: number }[]; title: string }) {
  return <ConsumptionTrendChart points={points} title={title} description="Litres wasted per day" showWastage={false} />;
}