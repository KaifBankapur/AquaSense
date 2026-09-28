import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { fmtLiters, fmtPct } from "@/lib/format";

interface BarRow {
  name: string;
  value: number;
  secondary?: number;
  [key: string]: any;
}

interface Props {
  data: BarRow[];
  valueKey?: string;
  color?: string;
  height?: number;
  valueFormatter?: (v: number) => string;
  secondaryLabel?: string;
  dataKey?: string;
  name?: string;
  tooltipSecondary?: string;
}

const PALETTE = ["#0891b2", "#06b6d4", "#0e7490", "#67e8f9", "#155e75", "#22d3ee", "#164e63", "#38bdf8"];

function BarTip({ active, payload, label, formatter }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-md">
      <p className="mb-1 font-semibold">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} className="flex items-center gap-2">
          <span className="inline-block size-2 rounded-full" style={{ background: p.color }} />
          <span className="capitalize text-muted-foreground">{p.dataKey}:</span>
          <span className="font-medium tabular-nums">{formatter?.(p.value) ?? fmtLiters(p.value)}</span>
        </p>
      ))}
    </div>
  );
}

export function HorizontalBars({ data, color = "#0891b2", height = 300, valueFormatter }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 12, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={valueFormatter} />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={110}
        />
        <Tooltip content={<BarTip formatter={valueFormatter} />} cursor={{ fill: "hsl(var(--muted))", opacity: 0.5 }} />
        <Bar dataKey="value" name="value" radius={[0, 4, 4, 0]} barSize={18}>
          {data.map((_, i) => (
            <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function VerticalBars({
  data,
  color = "#0891b2",
  height = 260,
  valueFormatter,
  dataKey = "value",
  name = "value",
  tooltipSecondary,
}: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={10} />
        <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={54} tickFormatter={valueFormatter} />
        <Tooltip content={<BarTip formatter={valueFormatter} />} cursor={{ fill: "hsl(var(--muted))", opacity: 0.4 }} />
        <Bar dataKey={dataKey} name={name} fill={color} radius={[4, 4, 0, 0]} maxBarSize={42} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Compute a chart-scale color (blue→red) for wastage % values. */
export function pctColor(v: number, max = 30): string {
  const t = Math.min(1, Math.max(0, v / max));
  const r = Math.round(8 + t * 247);
  const g = Math.round(145 + (1 - t) * 70);
  const b = Math.round(177 - t * 150);
  return `rgb(${r},${g},${b})`;
}

export function usePctColor(values: number[], max = 30): string[] {
  return useMemo(() => values.map((v) => pctColor(v, max)), [values, max]);
}

export { fmtPct };