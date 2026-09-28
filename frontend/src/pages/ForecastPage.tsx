import { useMemo, useState } from "react";

import { ForecastChart } from "@/charts/ForecastChart";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ErrorState, LoadingState } from "@/components/States";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtLiters, fmtNum, shortLabel } from "@/lib/format";

export function ForecastPage() {
  const forecast = useApi(() => api.forecast(), []);
  const [horizon, setHorizon] = useState<"7d" | "30d">("7d");
  const d = forecast.data;
  const points = useMemo(
    () => (d ? (horizon === "7d" ? d.forecast_7d.points : d.forecast_30d.points) : []),
    [d, horizon],
  );

  return (
    <div>
      <PageHeader
        title="Demand Forecast"
        description="Water demand predictions from the Spark ML model — historic actuals plus 7 and 30 day forecasts with confidence intervals."
      />

      {forecast.loading ? (
        <LoadingState />
      ) : forecast.error || !d ? (
        <ErrorState message={forecast.error ?? "forecast unavailable"} onRetry={forecast.reload} />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard label="Model" value={d.method} hint={`trained on ${fmtNum(d.trained_on_days)} days`} icon="sparkles" accent="green" />
            <StatCard label="RMSE" value={`${fmtNum(d.model_metrics.rmse)} L`} hint="root mean squared error" icon="scale" accent="blue" />
            <StatCard label="MAE" value={`${fmtNum(d.model_metrics.mae)} L`} hint="mean absolute error" icon="scale" accent="cyan" />
            <StatCard
              label={`Next ${horizon}`}
              value={fmtLiters(points[0]?.predicted ?? 0)}
              hint="one-step ahead prediction"
              icon="calendar"
              accent="amber"
            />
          </div>

          <Card className="mt-6 card-hover">
            <CardHeader className="flex-row items-start justify-between">
              <div>
                <CardTitle>Forecast vs actuals</CardTitle>
                <CardDescription>
                  Solid cyan = measured history · dashed amber = model prediction · shaded band = 95% confidence interval
                </CardDescription>
              </div>
              <Tabs value={horizon} onValueChange={(v) => setHorizon(v as any)}>
                <TabsList>
                  <TabsTrigger value="7d">7 days</TabsTrigger>
                  <TabsTrigger value="30d">30 days</TabsTrigger>
                </TabsList>
              </Tabs>
            </CardHeader>
            <CardContent>
              <ForecastChart forecast={d} horizon={horizon} />
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Forecast table — next {horizon}</CardTitle>
              <CardDescription>Predicted city-wide daily demand with lower/upper bounds</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="grid gap-2 p-4 sm:grid-cols-2 lg:grid-cols-4">
                {points.map((p) => (
                  <div key={p.date} className="rounded-lg border bg-card p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{shortLabel(p.date)}</span>
                      <Badge variant="warning" className="text-[10px]">
                        forecast
                      </Badge>
                    </div>
                    <p className="mt-1.5 text-lg font-bold tabular-nums">{fmtLiters(p.predicted)}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {fmtLiters(p.lower)} – {fmtLiters(p.upper)}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <p className="mt-4 text-xs text-muted-foreground">
            {d.disclaimer ?? "Forecast values are model predictions, not measured data."}
          </p>
        </>
      )}
    </div>
  );
}