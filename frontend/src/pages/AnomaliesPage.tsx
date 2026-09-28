import { useMemo, useState } from "react";

import { VerticalBars } from "@/charts/Bars";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ErrorState, LoadingState } from "@/components/States";
import { useApi } from "@/hooks/useApi";
import { useAreas } from "@/hooks/useAreas";
import { api } from "@/lib/api";
import { fmtLiters, fmtNum, fmtPct } from "@/lib/format";
import type { AnomalyEvent } from "@/types/analytics";

const SEVERITIES = ["critical", "high", "medium", "low"];
const CLASS_COLORS: Record<string, "destructive" | "warning" | "info" | "success"> = {
  ANOMALY: "destructive",
  POSSIBLE_LEAKAGE: "warning",
  HIGH: "info",
  NORMAL: "success",
};

function severityBadge(s: string): "destructive" | "warning" | "info" | "secondary" {
  if (s === "critical") return "destructive";
  if (s === "high") return "warning";
  if (s === "medium") return "info";
  return "secondary";
}

export function AnomaliesPage() {
  const areas = useAreas();
  const [areaId, setAreaId] = useState("");
  const [severity, setSeverity] = useState("");
  const [building, setBuilding] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [page, setPage] = useState(1);

  const anomalies = useApi(
    () =>
      api.anomalies({
        area_id: areaId || undefined,
        severity: severity || undefined,
        building_type: building || undefined,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        page,
        page_size: 20,
      }),
    [areaId, severity, building, fromDate, toDate, page],
  );

  const summary = useApi(() => api.anomaliesSummary(), []);

  const events = anomalies.data?.events ?? ([] as AnomalyEvent[]);
  const totalFlagged = anomalies.data?.total_flagged ?? 0;
  const byAreaData = useMemo(() => {
    const rows = anomalies.data?.by_area ?? [];
    return rows.map((r) => ({ name: r.area_name, value: r.count }));
  }, [anomalies.data]);

  const resetFilters = () => {
    setAreaId("");
    setSeverity("");
    setBuilding("");
    setFromDate("");
    setToDate("");
    setPage(1);
  };

  return (
    <div>
      <PageHeader
        title="Anomalies"
        description="Statistical outliers and possible leaks identified by the Spark anomaly detector (z-score + deviation rules)."
      />

      {/* summary stats */}
      {summary.data ? (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <StatCard label="Total flagged" value={fmtNum(summary.data.total_flagged)} icon="bug" accent="red" />
          <StatCard
            label="Leak-like"
            value={fmtNum(summary.data.counts?.POSSIBLE_LEAKAGE ?? 0)}
            icon="alert-triangle"
            accent="amber"
          />
          <StatCard
            label="Hard anomalies"
            value={fmtNum(summary.data.counts?.ANOMALY ?? 0)}
            icon="activity"
            accent="red"
          />
          <StatCard
            label="High consumption"
            value={fmtNum(summary.data.counts?.HIGH ?? 0)}
            icon="activity"
            accent="blue"
          />
        </div>
      ) : null}

      {/* filters */}
      <Card className="mt-6">
        <CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-6">
          <Select value={areaId} onChange={(e) => { setAreaId(e.target.value); setPage(1); }}>
            <option value="">All areas</option>
            {areas.areas.map((a) => (
              <option key={a.area_id} value={a.area_id}>
                {a.area_name}
              </option>
            ))}
          </Select>
          <Select value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1); }}>
            <option value="">Any severity</option>
            {SEVERITIES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
          <Select value={building} onChange={(e) => { setBuilding(e.target.value); setPage(1); }}>
            <option value="">Any building type</option>
            {["residential", "commercial", "industrial", "institutional", "public"].map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </Select>
          <Input type="date" value={fromDate} onChange={(e) => { setFromDate(e.target.value); setPage(1); }} aria-label="From date" />
          <Input type="date" value={toDate} onChange={(e) => { setToDate(e.target.value); setPage(1); }} aria-label="To date" />
          <Button variant="outline" onClick={resetFilters}>
            Reset
          </Button>
        </CardContent>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Detected events
              <Badge variant="outline">{fmtNum(totalFlagged)} total</Badge>
            </CardTitle>
            <CardDescription>Sorted by deviation from expected consumption (largest first)</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {anomalies.loading ? (
              <LoadingState />
            ) : anomalies.error ? (
              <div className="p-5">
                <ErrorState message={anomalies.error} onRetry={anomalies.reload} />
              </div>
            ) : events.length === 0 ? (
              <p className="p-6 text-sm text-muted-foreground">No anomalies match these filters.</p>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Area</TableHead>
                      <TableHead>Household</TableHead>
                      <TableHead className="text-right">Consumed</TableHead>
                      <TableHead className="text-right">Expected</TableHead>
                      <TableHead className="text-right">Deviation</TableHead>
                      <TableHead className="text-right">z-score</TableHead>
                      <TableHead>Class</TableHead>
                      <TableHead>Severity</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {events.map((e, i) => (
                      <TableRow key={i}>
                        <TableCell className="whitespace-nowrap tabular-nums">{e.timestamp}</TableCell>
                        <TableCell className="font-medium">{e.area_name}</TableCell>
                        <TableCell className="font-mono text-xs">{e.household_id}</TableCell>
                        <TableCell className="text-right tabular-nums">{fmtLiters(e.consumed_water_liters)}</TableCell>
                        <TableCell className="text-right tabular-nums">{fmtLiters(e.expected_liters)}</TableCell>
                        <TableCell className="text-right tabular-nums font-semibold text-red-500">
                          +{fmtPct(e.deviation_pct, 1)}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">{e.z_score?.toFixed(2)}</TableCell>
                        <TableCell>
                          <Badge variant={CLASS_COLORS[e.anomaly_class] ?? "secondary"}>{e.anomaly_class}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={severityBadge(e.severity)}>{e.severity}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {anomalies.data && anomalies.data.pages > 1 ? (
                  <div className="flex items-center justify-between border-t px-4 py-3">
                    <span className="text-xs text-muted-foreground">
                      Page {anomalies.data.page} of {anomalies.data.pages}
                    </span>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page <= 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page >= (anomalies.data?.pages ?? 1)}
                        onClick={() => setPage((p) => p + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                ) : null}
              </>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Anomalies by area</CardTitle>
            <CardDescription>Flagged events per area (current filters)</CardDescription>
          </CardHeader>
          <CardContent>
            {byAreaData.length ? (
              <VerticalBars data={byAreaData} valueFormatter={(v) => fmtNum(Number(v))} color="#ef4444" />
            ) : (
              <p className="py-8 text-center text-sm text-muted-foreground">No data for current filters.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}