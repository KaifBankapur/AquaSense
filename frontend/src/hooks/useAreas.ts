import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import type { Area } from "@/types/analytics";

/** Shared area list used by filter dropdowns and area pages. */
export function useAreas() {
  const state = useApi(() => api.areas(), []);
  return {
    ...state,
    areas: (state.data?.areas ?? []) as Area[],
  };
}