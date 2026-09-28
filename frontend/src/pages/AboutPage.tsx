import {
  ArrowDown,
  ArrowRight,
  BarChart3,
  Bot,
  Database,
  FileJson,
  FlaskConical,
  Github,
  Layers,
  Server,
  Sparkles,
  Waves,
} from "lucide-react";
import { Link } from "react-router-dom";

import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";

const STEPS = [
  { title: "Synthetic dataset", desc: "Generator scripts create hourly per-household meter readings — realistic supply, consumption, weather and meter-status fields." },
  { title: "Spark ingestion", desc: "PySpark reads the CSV in parallel, infers schema and partitions by year/month." },
  { title: "Cleaning & quality", desc: "Nulls, out-of-range values, corrupt rows and duplicates are removed with full quality reporting." },
  { title: "Analytics", desc: "Totals, areas, peaks, wastage, households and time-series aggregations written as JSON + Parquet." },
  { title: "Anomaly detection", desc: "Rolling z-scores + deviation rules flag ANOMALY, POSSIBLE_LEAKAGE and HIGH consumption events." },
  { title: "Forecasting", desc: "Seasonal linear regression trained on daily demand history to predict the next 7 and 30 days." },
  { title: "FastAPI service", desc: "Serves the analytics plus filtered, pushdown-optimised queries over the Parquet layer." },
  { title: "Dashboard + AquaAI", desc: "React dashboard renders the numbers; the assistant answers questions using the same tools." },
];

export function AboutPage() {
  const health = useApi(() => api.health(), []);
  const dataset = useApi(() => api.datasetInfo().catch(() => null), []);

  return (
    <div>
      <PageHeader
        title="About this project"
        description="Smart Water Consumption Analytics — an end-to-end Big Data project on a real, reproducible pipeline."
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card className="card-hover p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Dataset records</p>
          <p className="mt-2 text-xl font-bold">{dataset.data ? Number(dataset.data.total_rows ?? 0).toLocaleString() : health.data ? "—" : "—"}</p>
          <p className="text-xs text-muted-foreground">synthetic hourly readings</p>
        </Card>
        <Card className="card-hover p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Monitoring areas</p>
          <p className="mt-2 text-xl font-bold">{dataset.data ? dataset.data.areas : "—"}</p>
          <p className="text-xs text-muted-foreground">zones across the city</p>
        </Card>
        <Card className="card-hover p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Households</p>
          <p className="mt-2 text-xl font-bold">{dataset.data ? Number(dataset.data.households ?? 0).toLocaleString() : "—"}</p>
          <p className="text-xs text-muted-foreground">per district</p>
        </Card>
        <Card className="card-hover p-5">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Analytics layer</p>
          <p className="mt-2 text-xl font-bold">Parquet</p>
          <p className="text-xs text-muted-foreground">columnar, partition-pruned</p>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Architecture</CardTitle>
          <CardDescription>How data flows through the system</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <Chip icon={FlaskConical} label="Generator (CSV)" />
            <ArrowRight className="size-4 text-muted-foreground" />
            <Chip icon={Database} label="Spark ingestion" />
            <ArrowRight className="size-4 text-muted-foreground" />
            <Chip icon={Layers} label="Cleaning + quality" />
            <ArrowRight className="size-4 text-muted-foreground" />
            <Chip icon={BarChart3} label="Analytics" />
            <ArrowRight className="size-4 text-muted-foreground" />
            <Chip icon={FileJson} label="Parquet + JSON" />
            <ArrowRight className="size-4 text-muted-foreground" />
            <Chip icon={Server} label="FastAPI" />
            <ArrowRight className="size-4 text-muted-foreground" />
            <Chip icon={Waves} label="React dashboard" />
          </div>
          <div className="mt-6 space-y-0">
            {STEPS.map((s, i) => (
              <div key={s.title} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="flex size-7 items-center justify-center rounded-full bg-primary/12 text-xs font-bold text-primary">
                    {i + 1}
                  </div>
                  {i < STEPS.length - 1 ? <div className="h-full w-px bg-border" /> : null}
                </div>
                <div className="pb-5">
                  <p className="text-sm font-semibold">{s.title}</p>
                  <p className="mt-0.5 max-w-2xl text-xs text-muted-foreground">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Stack</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {["Python 3.14", "PySpark 4", "Apache Spark", "Parquet", "PyArrow", "FastAPI", "SQLAlchemy", "React 18", "TypeScript", "Tailwind CSS", "shadcn/ui", "Recharts", "assistant-ui", "Docker Compose"].map((t) => (
              <Badge key={t} variant="secondary">
                {t}
              </Badge>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Introspection & honesty</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>
              Every number in this dashboard is computed by the Spark pipeline and served by the backend — including the
              AquaAI assistant, which only answers from the same analytics API.
            </p>
            <p>
              Forecast values are explicitly labelled as{" "}
              <Badge variant="warning">predictions</Badge>, never measurements.
            </p>
            <p>
              Run the full stack with{" "}
              <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">docker compose up</code> — or locally:{" "}
              <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">python scripts/run_pipeline.py</code> then{" "}
              <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">npm run dev</code>.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link to="/assistant">
          <Button>
            <Bot className="size-4" /> Try AquaAI
          </Button>
        </Link>
        <Link to="/data">
          <Button variant="outline">
            <Database className="size-4" /> Explore the raw data
          </Button>
        </Link>
        <Button variant="ghost" onClick={() => window.open("https://spark.apache.org", "_blank")}>
          <Sparkles className="size-4" /> Apache Spark
        </Button>
      </div>

      <p className="mt-8 flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
        <ArrowDown className="size-3" /> Academic project — data is synthetic. <Github className="ml-1 size-3" />
      </p>
    </div>
  );
}

function Chip({ icon: Icon, label }: { icon: typeof FlaskConical; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border bg-card px-3 py-1.5 text-xs font-medium shadow-sm">
      <Icon className="size-3.5 text-primary" /> {label}
    </span>
  );
}