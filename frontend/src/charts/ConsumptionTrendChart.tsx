import { useMemo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TrendPoint } from "@/types/analytics";
import { fmtLiters } from "@/lib/format";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  points: TrendPoint[];
  title?: string;
  description?: string;
  height?: number;
  showWastage?: boolean;
}

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-semibold">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} className="flex items-center gap-2">
          <span className="inline-block size-2 rounded-full" style={{ background: p.color }} />
          <span className="capitalize text-muted-foreground">{p.dataKey}:</span>
          <span className="font-medium tabular-nums">{fmtLiters(p.value)}</span>
        </p>
      ))}
    </div>
  );
}

export function ConsumptionTrendChart({ points, title, description, height = 280, showWastage = true }: Props) {
  const data = useMemo(() => points.map((p) => ({ ...p, key: p.label })), [points]);
  if (!data.length) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">No trend data.</CardContent>
      </Card>
    );
  }
  const tickCount = Math.min(6, data.length);
  return (
    <Card className="card-hover">
      <CardHeader>
        {title ? <CardTitle>{title}</CardTitle> : null}
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="gConsumed" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-primary, #0891b2)" stopOpacity={0.35} />
                <stop offset="100%" stopColor="var(--color-primary, #0891b2)" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="gWastage" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
              minTickGap={28}
              tickCount={tickCount}
            />
            <YAxis
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              width={58}
              tickFormatter={(v: number) => fmtLiters(v)}
            />
            <Tooltip content={<ChartTooltip />} />
            <Area
              type="monotone"
              dataKey="consumed"
              name="consumed"
              stroke="#0891b2"
              strokeWidth={2}
              fill="url(#gConsumed)"
            />
            {showWastage ? (
              <Area
                type="monotone"
                dataKey="wastage"
                name="wastage"
                stroke="#f59e0b"
                strokeWidth={1.5}
                strokeDasharray="4 3"
                fill="url(#gWastage)"
              />
            ) : null}
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}