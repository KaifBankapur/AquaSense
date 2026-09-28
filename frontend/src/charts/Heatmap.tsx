import { useMemo } from "react";

import { cn } from "@/lib/utils";
import { fmtLiters } from "@/lib/format";

interface CellData {
  day_of_week: number;
  day_name: string;
  hour: number;
  liters: number;
  share_pct: number;
}

const DAY_KEYS = [
  { key: 0, name: "Mon" },
  { key: 1, name: "Tue" },
  { key: 2, name: "Wed" },
  { key: 3, name: "Thu" },
  { key: 4, name: "Fri" },
  { key: 5, name: "Sat" },
  { key: 6, name: "Sun" },
];

/** Blue → red color scale for consumption intensity. */
function intensityColor(sharePct: number): string {
  const t = Math.min(1, Math.max(0, (sharePct - 0.15) / 0.85));
  if (t < 0.4) {
    const k = t / 0.4;
    return `rgba(8, 145, 178, ${0.15 + k * 0.55})`;
  }
  const k = (t - 0.4) / 0.6;
  return `rgba(245, 158, 11, ${0.1 + k * 0.75})`;
}

export function WeekHourHeatmap({ cells }: { cells: CellData[] }) {
  const byDay = useMemo(() => {
    const map: Record<number, Map<number, CellData>> = {};
    for (const cell of cells) {
      if (!map[cell.day_of_week]) map[cell.day_of_week] = new Map();
      map[cell.day_of_week].set(cell.hour, cell);
    }
    return map;
  }, [cells]);

  const selected = useMemo(() => {
    let max: CellData | null = null;
    for (const c of cells) if (!max || c.liters > max.liters) max = c;
    return max;
  }, [cells]);

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[640px]">
        <div className="grid grid-cols-[64px_repeat(24,1fr)] gap-1">
          <div />
          {Array.from({ length: 24 }, (_, h) => (
            <div key={h} className="text-center text-[10px] text-muted-foreground">
              {h % 3 === 0 ? `${h}` : ""}
            </div>
          ))}
          {DAY_KEYS.map((day) => (
            <div key={day.key} className="grid grid-cols-subgrid col-span-25 gap-1" style={{ gridTemplateColumns: "64px repeat(24,1fr)" }}>
              <div className="flex items-center text-[11px] font-medium text-muted-foreground">{day.name}</div>
              {Array.from({ length: 24 }, (_, h) => {
                const cell = byDay[day.key]?.get(h);
                const isPeak = cell && selected && cell.liters === selected.liters;
                return (
                  <div
                    key={h}
                    title={cell ? `${day.name} ${String(h).padStart(2, "0")}:00 · ${fmtLiters(cell.liters)}` : "—"}
                    className={cn("h-5 rounded-[4px] transition-transform hover:scale-110", !cell && "bg-muted/40")}
                    style={cell ? { background: intensityColor(cell.share_pct) } : undefined}
                  >
                    {isPeak ? (
                      <div className="flex h-full items-center justify-center text-[9px] font-bold text-white">★</div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
        {selected ? (
          <p className="mt-3 text-xs text-muted-foreground">
            Peak cell — <span className="font-semibold text-foreground">{selected.day_name} {String(selected.hour).padStart(2, "0")}:00</span> ·{" "}
            {fmtLiters(selected.liters)} ({selected.share_pct.toFixed(2)}% of total).
          </p>
        ) : null}
      </div>
    </div>
  );
}