import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { Hero } from "@/components/Hero";
import type { DashboardSummary, WastageResponse } from "@/types/analytics";

// framer-motion uses IntersectionObserver for whileInView — stub it for jsdom
vi.stubGlobal(
  "IntersectionObserver",
  class {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  },
);

const summary: DashboardSummary = {
  total_consumed_liters: 13146155.2,
  total_supplied_liters: 13768722.4,
  total_wastage_liters: 622567.2,
  wastage_rate_pct: 4.52,
  peak_consumption_liters: 522.0,
  active_areas: 10,
  record_count: 350400,
  avg_consumption: 37.52,
  peak_hour: 19,
  peak_area_name: "Old Hubballi",
  peak_day_name: "Mon",
  generated_at: "2026-09-24T00:14:12",
};

const wastage = { leak_event_count: 397 } as unknown as WastageResponse;

// Animation-split text (Stagger/Flip/Morph) lives in nested spans, so assert
// against the composed text content rather than direct text nodes.
describe("Hero", () => {
  it("renders the animated headline, morph words, live chips and analytics", () => {
    const view = render(
      <MemoryRouter>
        <Hero summary={summary} wastage={wastage} />
      </MemoryRouter>,
    );
    // stagger/flip join words with NBSP — normalize before matching
    const text = (view.container.textContent ?? "").replace(/\u00A0/g, " ");

    // animated headline + subtitle keep their full text in the DOM
    expect(text).toContain("See where every drop goes");
    expect(text).toContain("Big-data water analytics");

    // CTAs
    expect(text).toContain("Explore analytics");
    expect(text).toContain("Ask AquaAI");

    // all morph words are present (rotation shows one at a time)
    for (const word of ["wastage", "undetected leaks", "demand spikes", "anomalies"]) {
      expect(text).toContain(word);
    }

    // live chips render real analytics (direct text labels)
    expect(screen.getByText("Consumed")).toBeInTheDocument();
    expect(screen.getByText("Leak events")).toBeInTheDocument();
  });

  it("falls back to placeholders while analytics load", () => {
    const view = render(
      <MemoryRouter>
        <Hero summary={null} wastage={null} />
      </MemoryRouter>,
    );
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(4);
    expect((view.container.textContent ?? "").replace(/\u00A0/g, " ")).toContain(
      "See where every drop goes",
    );
  });
});