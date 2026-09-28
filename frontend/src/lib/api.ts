/** Typed API client for the AquaSense backend. */

import type {
  AnomaliesResponse,
  Area,
  AreaDetail,
  AreasResponse,
  AssistantResponse,
  AssistantStatus,
  ChatTurn,
  DashboardSummary,
  DataQuality,
  DataResponse,
  DatasetInfo,
  Forecast,
  Health,
  KpiCard,
  PeaksResponse,
  PipelineMeta,
  TrendResponse,
  WastageResponse,
} from "@/types/analytics";

export const API_BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ??
  `${window.location.origin}/api`;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* not json */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  health: () => request<Health>("/health"),
  pipeline: () => request<PipelineMeta>("/pipeline"),
  datasetInfo: () => request<DatasetInfo>("/dataset/info"),

  dashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),
  kpis: () => request<KpiCard[]>("/dashboard/kpis"),
  trend: (p: {
    granularity?: "hourly" | "daily" | "weekly" | "monthly" | "yearly";
    from_date?: string;
    to_date?: string;
    area_id?: string;
    building_type?: string;
  }) => request<TrendResponse>(`/dashboard/trend${qs(p)}`),

  areas: () => request<AreasResponse>("/areas"),
  areaDetail: (areaId: string) => request<AreaDetail>(`/areas/${areaId}`),
  compare: (ids: string[]) => request<{ areas: Area[]; count: number }>(`/areas/compare${qs({ area_ids: ids.join(",") })}`),

  wastage: () => request<WastageResponse>("/wastage"),
  wastageLeaks: () =>
    request<{ leak_events: WastageResponse["leak_events"]; leak_event_count: number; threshold_pct: number }>(
      "/wastage/leaks",
    ),

  peaks: () => request<PeaksResponse>("/peak"),
  forecast: () => request<Forecast>("/forecast"),
  quality: () => request<DataQuality>("/data-quality"),

  anomalies: (p: {
    area_id?: string;
    from_date?: string;
    to_date?: string;
    severity?: string;
    building_type?: string;
    page?: number;
    page_size?: number;
  }) => request<AnomaliesResponse>(`/anomalies${qs(p)}`),
  anomaliesSummary: () =>
    request<Pick<AnomaliesResponse, "counts" | "total_flagged" | "severity_counts" | "by_area">>("/anomalies/summary"),

  dataRows: (p: {
    page?: number;
    page_size?: number;
    search?: string;
    sort_by?: string;
    sort_desc?: boolean;
    from_date?: string;
    to_date?: string;
    area_id?: string;
    building_type?: string;
    zone?: string;
  }) => request<DataResponse>(`/data${qs(p)}`),
  dataColumns: () => request<{ columns: string[] }>("/data/columns"),

  assistantStatus: () => request<AssistantStatus>("/assistant/status"),
  assistantChat: (turn: ChatTurn) =>
    request<AssistantResponse>("/assistant/chat", {
      method: "POST",
      body: JSON.stringify(turn),
    }),
};