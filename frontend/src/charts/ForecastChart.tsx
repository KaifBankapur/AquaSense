import { useMemo } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { Forecast } from "@/types/analytics";
import { fmtLiters } from "@/lib/format";

function FxTip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-semibold">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} className="flex items-center gap-2">
          <span className="inline-block size-2 rounded-full" style={{ background: p.color }} />
          <span className="text-muted-foreground">{p.dataKey}:</span>
          <span className="font-medium tabular-nums">{p.dataKey === "Interval" ? `${fmtLiters(p.payload.lower)}–${fmtLiters(p.payload.upper)}` : fmtLiters(p.value)}</span>
        </p>
      ))}
    </div>
  );
}

export function ForecastChart({ forecast, horizon = "7d" }: { forecast: Forecast; horizon?: "7d" | "30d" }) {
  const data = useMemo(() => {
    const fc = horizon === "7d" ? forecast.forecast_7d : forecast.forecast_30d;
    const hist = forecast.history.slice(horizon === "7d" ? -42 : -60).map((p) => ({
      label: p.date,
      consumed: p.consumed,
    }));
    const forecastPts = fc.points.map((p) => ({
      label: p.date,
      predicted: p.predicted,
      lower: p.lower,
      upper: p.upper,
    }));
    return { hist, forecastPts };
  }, [forecast, horizon]);

  const isReal = (d: any) => d.consumed !== undefined && d.predicted === undefined;

  return (
    <div>
      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart
          data={[...data.hist, ...data.forecastPts]}
          margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="gCi" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.28} />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} minTickGap={30} />
          <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={58} tickFormatter={(v: number) => fmtLiters(v)} />
          <Tooltip content={<FxTip />} />
          <Area dataKey="interval" name="Interval" stroke="none" fill="url(#gCi)" connectNulls={false} />
          <ReferenceLine x={data.hist.at(-1)?.label} stroke="hsl(var(--muted-foreground))" strokeDasharray="4 3" label={{ value: "now", position: "top", fontSize: 10 }} />
          <Line dataKey="consumed" name="Actual" stroke="#0891b2" strokeWidth={2} dot={false} connectNulls />
          <Line dataKey="predicted" name="Predicted" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 2.5, fill: "#f59e0b" }} strokeDasharray="6 3" connectNulls />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}