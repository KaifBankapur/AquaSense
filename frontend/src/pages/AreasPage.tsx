import { ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";

import { HorizontalBars } from "@/charts/Bars";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ErrorState, LoadingState } from "@/components/States";
import { useAreas } from "@/hooks/useAreas";
import { fmtLiters, fmtNum, fmtPct } from "@/lib/format";

export function AreasPage() {
  const { data, loading, error, reload, areas } = useAreas();

  return (
    <div>
      <PageHeader
        title="Service Areas"
        description="Consumption and efficiency ranking across all monitored areas."
        actions={
          <div className="grid grid-cols-2 gap-2">
            <StatCard label="Areas" value={data ? fmtNum(data.count) : "—"} accent="blue" className="p-3" />
            <StatCard
              label="Households"
              value={data ? fmtNum(areas.reduce((s, a) => s + a.household_count, 0)) : "—"}
              accent="green"
              className="p-3"
            />
          </div>
        }
      />

      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Consumption vs wastage by area</CardTitle>
              <CardDescription>Total litres consumed per area (bars) with wastage share (label)</CardDescription>
            </CardHeader>
            <CardContent>
              <HorizontalBars
                data={areas.map((a) => ({ name: a.area_name, value: a.total_consumed }))}
                valueFormatter={(v) => fmtLiters(Number(v))}
              />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Area</TableHead>
                    <TableHead className="text-right">Rank</TableHead>
                    <TableHead className="text-right">Consumed</TableHead>
                    <TableHead className="text-right">Supplied</TableHead>
                    <TableHead className="text-right">Wastage</TableHead>
                    <TableHead className="text-right">Wastage %</TableHead>
                    <TableHead className="text-right">Avg L/h</TableHead>
                    <TableHead className="text-right">Households</TableHead>
                    <TableHead className="text-right">Peak hour</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {areas.map((a) => (
                    <TableRow key={a.area_id} className="cursor-pointer">
                      <TableCell>
                        <div className="font-medium">{a.area_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {a.area_id} · {a.zone} zone
                        </div>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        <Badge variant="secondary">#{a.rank}</Badge>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(a.total_consumed)}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(a.total_supplied)}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(a.total_wastage)}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        <Badge variant={a.wastage_rate_pct > 5 ? "warning" : "success"}>{fmtPct(a.wastage_rate_pct)}</Badge>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(a.avg_consumption)}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtNum(a.household_count)}</TableCell>
                      <TableCell className="text-right tabular-nums">{String(a.peak_hour).padStart(2, "0")}:00</TableCell>
                      <TableCell>
                        <Link to={`/areas/${a.area_id}`}>
                          <Button variant="ghost" size="icon" aria-label={`Open ${a.area_name}`}>
                            <ArrowUpRight className="size-4" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Side-by-side comparison</CardTitle>
              <CardDescription>Consumption, wastage and efficiency across all areas</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Area</TableHead>
                    <TableHead className="text-right">Consumed</TableHead>
                    <TableHead className="text-right">Wastage</TableHead>
                    <TableHead className="text-right">Wastage %</TableHead>
                    <TableHead className="text-right">Avg L/h</TableHead>
                    <TableHead className="text-right">Avg / household</TableHead>
                    <TableHead className="text-right">Peak hour</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {areas.map((a) => (
                    <TableRow key={a.area_id}>
                      <TableCell className="font-medium">{a.area_name}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(a.total_consumed)}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(a.total_wastage)}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        <Badge variant={a.wastage_rate_pct > 5 ? "warning" : "success"}>{fmtPct(a.wastage_rate_pct)}</Badge>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(a.avg_consumption)}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(a.avg_household_consumption)}</TableCell>
                      <TableCell className="text-right tabular-nums">{String(a.peak_hour).padStart(2, "0")}:00</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}