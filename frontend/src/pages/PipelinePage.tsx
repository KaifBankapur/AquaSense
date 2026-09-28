import { useMemo } from "react";
import { BarChart2, CheckCircle2, Cpu, FileJson, FolderTree, Timer } from "lucide-react";

import { VerticalBars } from "@/charts/Bars";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/States";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtNum, secondsToClock } from "@/lib/format";

const STAGE_LABELS: Record<string, string> = {
  ingestion: "Ingestion",
  preprocessing: "Preprocessing",
  quality: "Data quality",
  "analytics.totals": "Totals",
  "analytics.areas": "Areas",
  "analytics.peaks": "Peaks",
  "analytics.wastage": "Wastage",
  "analytics.households": "Households",
  "analytics.timeseries": "Time series",
  "anomaly.detection": "Anomaly detection",
  forecasting: "Forecasting",
};

export function PipelinePage() {
  const pipeline = useApi(() => api.pipeline(), []);
  const d = pipeline.data;

  const stages = useMemo(() => {
    const times = d?.stage_times_seconds ?? {};
    return Object.entries(times)
      .map(([key, seconds]) => ({
        name: STAGE_LABELS[key] ?? key,
        key,
        seconds: Number(seconds.toFixed(2)),
      }))
      .sort((a, b) => b.seconds - a.seconds);
  }, [d]);

  return (
    <div>
      <PageHeader
        title="Spark Pipeline"
        description="How the big-data layer turns raw meter readings into the analytics this dashboard serves."
      />

      {pipeline.loading ? (
        <LoadingState />
      ) : pipeline.error || !d ? (
        <ErrorState message={pipeline.error ?? "pipeline metadata unavailable"} onRetry={pipeline.reload} />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Card className="card-hover p-5">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Last run</p>
              <p className="mt-2 text-lg font-bold">{d.ran_at?.replace("T", " ")}</p>
            </Card>
            <Card className="card-hover p-5">
              <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                <Timer className="size-3.5" /> Total duration
              </p>
              <p className="mt-2 text-lg font-bold">{secondsToClock(d.total_seconds ?? 0)}</p>
            </Card>
            <Card className="card-hover p-5">
              <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                <Cpu className="size-3.5" /> Records processed
              </p>
              <p className="mt-2 text-lg font-bold">{fmtNum(d.processed_records)}</p>
            </Card>
            <Card className="card-hover p-5">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Spark version</p>
              <p className="mt-2 text-lg font-bold">{d.cluster?.version}</p>
              <p className="text-xs text-muted-foreground">{d.cluster?.master}</p>
            </Card>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Stage execution time</CardTitle>
                <CardDescription>Seconds per pipeline stage in the last run</CardDescription>
              </CardHeader>
              <CardContent>
                <VerticalBars
                  data={stages.map((s) => ({ name: s.name, value: s.seconds }))}
                  valueFormatter={(v) => `${Number(v).toFixed(0)}s`}
                  color="#0891b2"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Cluster</CardTitle>
                <CardDescription>Spark session configuration</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <Row k="Application" v={d.cluster?.app_name ?? "—"} />
                <Row k="Master" v={d.cluster?.master ?? "—"} />
                <Row k="Default parallelism" v={String(d.cluster?.default_parallelism ?? "—")} />
                <Row k="Spark UI" v={d.cluster?.spark_ui ?? "—"} mono />
                <Row k="Areas processed" v={String(d.areas ?? "—")} />
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderTree className="size-4 text-primary" /> Outputs
              </CardTitle>
              <CardDescription>Artifacts written by the pipeline</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-lg border p-4">
                <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
                  <BarChart2 className="size-4 text-primary" /> Cleaned Parquet
                </p>
                <p className="break-all font-mono text-xs text-muted-foreground">{d.outputs?.clean_parquet}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Partitioned by year / month for columnar pushdown reads.
                </p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
                  <FileJson className="size-4 text-primary" /> JSON analytics
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {d.outputs?.analytics_files.map((f) => (
                    <Badge key={f} variant="outline" className="font-mono text-[10px]">
                      {f}
                    </Badge>
                  ))}
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  Path: <span className="font-mono">{d.outputs?.analytics}</span>
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="mt-6 flex items-center gap-2 text-xs text-muted-foreground">
            <CheckCircle2 className="size-4 text-emerald-500" />
            All values are taken from the pipeline's own metadata file written at run time.
          </div>
        </>
      )}
    </div>
  );
}

function Row({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between border-b pb-2 last:border-0">
      <span className="text-muted-foreground">{k}</span>
      <span className={mono ? "font-mono text-xs" : "font-medium"}>{v}</span>
    </div>
  );
}