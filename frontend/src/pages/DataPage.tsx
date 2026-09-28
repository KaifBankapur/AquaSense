import { ChevronDown, ChevronUp, Download, Search } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ErrorState, LoadingState } from "@/components/States";
import { useApi } from "@/hooks/useApi";
import { useAreas } from "@/hooks/useAreas";
import { api } from "@/lib/api";
import { fmtLiters, fmtPct } from "@/lib/format";
import type { DataRow } from "@/types/analytics";

const PAGE_SIZES = [10, 25, 50, 100];
const SORTABLE = ["timestamp", "consumed_water_liters", "wastage_liters", "wastage_percent", "temperature_c"];

export function DataPage() {
  const areas = useAreas();
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [areaId, setAreaId] = useState("");
  const [building, setBuilding] = useState("");
  const [sortBy, setSortBy] = useState("timestamp");
  const [sortDesc, setSortDesc] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const data = useApi(
    () =>
      api.dataRows({
        search: debouncedSearch || undefined,
        area_id: areaId || undefined,
        building_type: building || undefined,
        sort_by: sortBy,
        sort_desc: sortDesc,
        page,
        page_size: pageSize,
      }),
    [debouncedSearch, areaId, building, sortBy, sortDesc, page, pageSize],
  );

  const rows = data.data?.rows ?? [];
  const pag = data.data?.pagination;

  const applySearch = () => {
    setDebouncedSearch(search.trim());
    setPage(1);
  };

  const toggleSort = (col: string) => {
    if (sortBy === col) setSortDesc((d) => !d);
    else {
      setSortBy(col);
      setSortDesc(col !== "timestamp");
    }
    setPage(1);
  };

  const exportCsv = () => {
    const params = new URLSearchParams({ resource: "data" });
    if (areaId) params.set("area_id", areaId);
    window.open(`${apiBase()}/export/csv?${params.toString()}`, "_blank");
  };

  return (
    <div>
      <PageHeader
        title="Data Explorer"
        description="Raw household-level readings from the Parquet analytical layer — paginated server-side."
        actions={
          <Button variant="outline" onClick={exportCsv}>
            <Download className="size-4" /> Export CSV
          </Button>
        }
      />

      <Card>
        <CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="flex gap-2">
            <Input
              placeholder="Search anything…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && applySearch()}
            />
            <Button variant="secondary" onClick={applySearch} aria-label="Search">
              <Search className="size-4" />
            </Button>
          </div>
          <Select value={areaId} onChange={(e) => { setAreaId(e.target.value); setPage(1); }}>
            <option value="">All areas</option>
            {areas.areas.map((a) => (
              <option key={a.area_id} value={a.area_id}>
                {a.area_name}
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
          <Select value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
            {PAGE_SIZES.map((s) => (
              <option key={s} value={s}>
                {s} rows / page
              </option>
            ))}
          </Select>
          <Select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              setPage(1);
            }}
          >
            {SORTABLE.map((s) => (
              <option key={s} value={s}>
                Sort by {s}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardContent className="p-0">
          {data.loading ? (
            <LoadingState />
          ) : data.error ? (
            <div className="p-5">
              <ErrorState message={data.error} onRetry={data.reload} />
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    {[
                      ["timestamp", "Timestamp"],
                      ["area_name", "Area"],
                      ["household_id", "Household"],
                      ["building_type", "Type"],
                      ["supplied_water_liters", "Supplied"],
                      ["consumed_water_liters", "Consumed"],
                      ["wastage_liters", "Wastage"],
                      ["wastage_percent", "Wastage %"],
                      ["temperature_c", "Temp"],
                      ["meter_status", "Meter"],
                    ].map(([key, label]) => (
                      <TableHead
                        key={key}
                        className="cursor-pointer select-none hover:text-foreground"
                        onClick={() => SORTABLE.includes(key) && toggleSort(key)}
                      >
                        <span className="inline-flex items-center gap-1">
                          {label}
                          {sortBy === key ? (
                            sortDesc ? (
                              <ChevronDown className="size-3" />
                            ) : (
                              <ChevronUp className="size-3" />
                            )
                          ) : SORTABLE.includes(key) ? (
                            <ChevronDown className="size-3 opacity-20" />
                          ) : null}
                        </span>
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((r, i) => (
                    <TableRow key={i}>
                      <TableCell className="whitespace-nowrap tabular-nums">{r.timestamp}</TableCell>
                      <TableCell className="font-medium">{r.area_name}</TableCell>
                      <TableCell className="font-mono text-xs">{r.household_id}</TableCell>
                      <TableCell className="capitalize">{r.building_type}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(num(r.supplied_water_liters))}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(num(r.consumed_water_liters))}</TableCell>
                      <TableCell className="text-right tabular-nums">{fmtLiters(num(r.wastage_liters))}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        <Badge variant={num(r.wastage_percent) > 5 ? "warning" : "secondary"}>{fmtPct(num(r.wastage_percent))}</Badge>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{num(r.temperature_c)?.toFixed(1)}°C</TableCell>
                      <TableCell>
                        <Badge variant={r.meter_status === "OK" ? "success" : "warning"}>{String(r.meter_status)}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {pag && pag.total > 0 ? (
                <div className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3">
                  <span className="text-xs text-muted-foreground">
                    {pag.total.toLocaleString()} matching records · page {pag.page} of {pag.pages}
                  </span>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" disabled={page >= (pag.pages ?? 1)} onClick={() => setPage((p) => p + 1)}>
                      Next
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="p-6 text-center text-sm text-muted-foreground">No records match.</p>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function num(v: DataRow[string]): number {
  return typeof v === "number" ? v : Number(v ?? 0);
}

function apiBase(): string {
  return (import.meta.env.VITE_API_BASE as string | undefined) ?? `${window.location.origin}/api`;
}