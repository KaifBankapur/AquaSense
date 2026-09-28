/** API types mirroring the FastAPI response schemas (real Spark-derived data). */

// ---- shared ----
export interface Health {
  status: string;
  service: string;
  version: string;
  spark: string;
  dataset_present: boolean;
}

// ---- dashboard ----
export interface DashboardSummary {
  total_consumed_liters: number;
  total_supplied_liters: number;
  total_wastage_liters: number;
  wastage_rate_pct: number;
  peak_consumption_liters: number;
  active_areas: number;
  record_count: number;
  avg_consumption: number;
  peak_hour: number;
  peak_area_name: string;
  peak_day_name: string;
  generated_at?: string | null;
}

export interface KpiCard {
  key: string;
  label: string;
  value: number;
  unit: string;
  icon: string;
  sparkline?: number[] | null;
}

export interface TrendPoint {
  label: string;
  consumed: number;
  wastage?: number;
}

export interface TrendResponse {
  granularity: string;
  points: TrendPoint[];
}

// ---- areas ----
export interface Area {
  area_id: string;
  area_name: string;
  zone: string;
  rank: number;
  total_supplied: number;
  total_consumed: number;
  total_wastage: number;
  wastage_rate_pct: number;
  efficiency_pct: number;
  avg_consumption: number;
  avg_household_consumption: number;
  household_count: number;
  population: number;
  peak_hour: number;
  peak_hour_liters: number;
}

export interface AreasResponse {
  areas: Area[];
  count: number;
}

export interface AreaCompareRow {
  area_id: string;
  area_name: string;
  total_consumed: number;
  total_wastage: number;
  avg_consumption: number;
  avg_household_consumption: number;
  wastage_rate_pct: number;
  peak_hour: number;
  household_count: number;
}

export interface HistBin {
  bucket: string;
  count: number;
}

export interface AreaDetail {
  area: Area;
  trend_daily: TrendPoint[];
  trend_hourly: TrendPoint[];
  wastage_daily: { label: string; wastage: number }[];
  household_distribution: HistBin[];
  anomaly_count: number;
  forecast: Forecast;
  comparison_vs_overall_avg: number;
  values: {
    total_consumed: number;
    total_wastage: number;
    wastage_rate_pct: number;
    avg_consumption: number;
    avg_household_consumption: number;
    peak_hour: number;
  };
}

export interface TopConsumer {
  household_id: string;
  area_name: string;
  building_type: string;
  total_consumed: number;
  avg_consumption: number;
}

// ---- wastage ----
export interface WastageByArea {
  area_id: string;
  area_name: string;
  wastage_liters: number;
  wastage_pct: number;
  supplied_liters: number;
}

export interface WastageResponse {
  total_wastage_liters: number;
  total_supplied_liters: number;
  wastage_rate_pct: number;
  avg_wastage_pct: number;
  max_wastage_single_hour: number;
  leak_threshold_pct: number;
  leak_event_count: number;
  by_area: WastageByArea[];
  by_building_type: { building_type: string; wastage_liters: number; wastage_pct: number; records: number }[];
  monthly_wastage: { year: number; month: number; wastage_liters: number; wastage_pct: number }[];
  daily_wastage: { date: string; wastage_liters: number; wastage_pct: number }[];
  leak_events: {
    timestamp: string;
    area_name: string;
    household_id: string;
    building_type: string;
    supplied_water_liters: number;
    consumed_water_liters: number;
    wastage_liters: number;
    wastage_percent: number;
  }[];
}

// ---- peaks ----
export interface PeaksResponse {
  peak_hour: { hour: number; liters: number; label: string };
  peak_day: { day: number; day_name: string; liters: number };
  peak_week: { week: number; week_start: string; liters: number };
  peak_month: { year: number; month: number; liters: number };
  peak_area: { area_id: string; area_name: string; liters: number };
  heatmap: { day_of_week: number; day_name: string; hour: number; liters: number; share_pct: number }[];
  total_liters: number;
}

// ---- forecast ----
export interface ForecastPoint {
  date: string;
  predicted: number;
  lower: number;
  upper: number;
}

export interface Forecast {
  method: string;
  features: string[];
  trained_on_days: number;
  history: { date: string; consumed: number }[];
  model_metrics: { mse: number; mae: number; rmse: number; residual_std: number; intercept: number };
  forecast_7d: { horizon_days: number; is_forecast: boolean; points: ForecastPoint[] };
  forecast_30d: { horizon_days: number; is_forecast: boolean; points: ForecastPoint[] };
  disclaimer?: string;
}

// ---- anomalies ----
export interface AnomalyEvent {
  timestamp: string;
  area_id: string;
  area_name: string;
  zone: string;
  household_id: string;
  building_type: string;
  consumed_water_liters: number;
  expected_liters: number;
  deviation_pct: number;
  z_score: number;
  wastage_percent: number;
  anomaly_class: string;
  severity: string;
}

export interface AnomaliesResponse {
  counts: Record<string, number>;
  total_flagged: number;
  severity_counts: Record<string, number>;
  by_area: { area_id: string; area_name: string; count: number }[];
  events: AnomalyEvent[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

// ---- data explorer ----
export interface DataRow {
  timestamp: string;
  date: string;
  hour: number;
  area_id: string;
  area_name: string;
  zone: string;
  household_id: string;
  building_type: string;
  supplied_water_liters: number;
  consumed_water_liters: number;
  wastage_liters: number;
  wastage_percent: number;
  temperature_c: number;
  rainfall_mm: number;
  pressure_bar: number;
  meter_status: string;
  consumption_category: string;
  [key: string]: string | number | null;
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export interface DataResponse {
  rows: DataRow[];
  pagination: Pagination;
}

// ---- data quality ----
export interface DataQuality {
  source: string;
  total_records_read: number;
  valid_records: number;
  invalid_records: number;
  corrupt_rows: number;
  invalid_rows: number;
  duplicates_removed: number;
  missing_values: number;
  avg_consumption: number;
  total_wastage: number;
}

// ---- pipeline ----
export interface PipelineMeta {
  ran_at?: string;
  cluster?: {
    app_name: string;
    master: string;
    version: string;
    default_parallelism: number;
    spark_ui: string;
  };
  stage_times_seconds?: Record<string, number>;
  total_seconds?: number;
  processed_records?: number;
  areas?: number;
  outputs?: { clean_parquet: string; analytics: string; analytics_files: string[] };
}

// ---- assistant ----
export interface AssistantToolCall {
  name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
}

export interface AssistantResponse {
  message: string;
  mode: "llm" | "local";
  tool_calls: AssistantToolCall[];
  suggestions: string[];
}

export interface AssistantStatus {
  name: string;
  mode: "llm" | "local";
  llm_configured: boolean;
  model: string | null;
}

export interface ChatTurn {
  content: string;
  history?: { role: "user" | "assistant"; content: string }[];
}

export interface DatasetInfo {
  generated_at: string;
  seed: number;
  base_rows: number;
  total_rows: number;
  households: number;
  areas: number;
  months: number;
  [key: string]: string | number | boolean | null;
}