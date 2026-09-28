import { ArrowLeft, MapPin, Users } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { ConsumptionTrendChart } from "@/charts/ConsumptionTrendChart";
import { VerticalBars } from "@/charts/Bars";
import { ForecastChart } from "@/charts/ForecastChart";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/States";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtLiters, fmtNum, fmtPct } from "@/lib/format";

export function AreaDetailPage() {
  const { areaId = "" } = useParams();
  const { data, loading, error, reload } = useApi(() => api.areaDetail(areaId), [areaId]);

  if (loading) return <LoadingState label="Loading area analytics…" />;
  if (error || !data)
    return (
      <div>
        <PageHeader title="Area detail" />
        <ErrorState message={error ?? "Area not found"} onRetry={reload} />
      </div>
    );

  const { area, comparison_vs_overall_avg } = data;
  const aboveAvg = comparison_vs_overall_avg > 0;

  return (
    <div>
      <Link
        to="/areas"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-4" /> All areas
      </Link>
      <PageHeader
        title={area.area_name}
        description={
          <span className="flex items-center gap-2">
            <MapPin className="size-3.5" /> {area.area_id} · {area.zone} zone · rank #{area.rank} by consumption
          </span>
        }
        actions={<Badge variant="info">{fmtLiters(area.total_consumed)} consumed</Badge>}
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total consumed" value={fmtLiters(area.total_consumed)} icon="droplets" accent="cyan" />
        <StatCard label="Total wastage" value={fmtLiters(area.total_wastage)} unit={fmtPct(area.wastage_rate_pct)} icon="alert-triangle" accent="red" />
        <StatCard label="Avg consumption" value={fmtLiters(area.avg_consumption)} unit="/h" icon="activity" accent="blue" />
        <StatCard
          label="Vs city average"
          value={`${aboveAvg ? "+" : ""}${fmtPct(comparison_vs_overall_avg)}`}
          hint={aboveAvg ? "consumes above city avg" : "consumes below city avg"}
          icon={aboveAvg ? "alert-triangle" : "water"}
          accent={aboveAvg ? "amber" : "green"}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
        <ConsumptionTrendChart
          points={data.trend_daily}
          title="Daily consumption trend"
          description={`${fmtNum(data.trend_daily.length)} days · litres consumed (cyan) vs wasted (amber)`}
        />
        <ConsumptionTrendChart
          points={data.trend_hourly}
          title="Hourly consumption trend"
          description="Hour-by-hour consumption across the full dataset"
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Household consumption distribution</CardTitle>
            <CardDescription>Number of households by total consumption bucket (litres)</CardDescription>
          </CardHeader>
          <CardContent>
            <VerticalBars
              data={data.household_distribution.map((b) => ({ name: b.bucket, value: b.count }))}
              valueFormatter={(v) => fmtNum(Number(v))}
              name="households"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Daily wastage</CardTitle>
            <CardDescription>Litres wasted per day in this area</CardDescription>
          </CardHeader>
          <CardContent>
            <VerticalBars
              data={data.wastage_daily.map((b) => ({ name: b.label, value: b.wastage }))}
              valueFormatter={(v) => fmtLiters(Number(v))}
              color="#f59e0b"
            />
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>7-day demand forecast for {area.area_name}</CardTitle>
          <CardDescription>
            Historical actuals compared with the Spark ML forecast (dashed amber = prediction)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ForecastChart forecast={data.forecast} />
        </CardContent>
      </Card>

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Households" value={fmtNum(area.household_count)} icon="users" accent="green" />
        <StatCard label="Population" value={fmtNum(area.population)} icon="users" accent="blue" />
        <StatCard label="Peak hour" value={`${String(area.peak_hour).padStart(2, "0")}:00`} hint={fmtLiters(area.peak_hour_liters)} icon="activity" accent="cyan" />
        <StatCard label="Anomalies flagged" value={fmtNum(data.anomaly_count)} icon="alert-triangle" accent="red" />
      </div>
    </div>
  );
}