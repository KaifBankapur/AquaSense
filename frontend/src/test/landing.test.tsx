import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { LandingPage } from "@/pages/LandingPage";

// The 21st.dev SaaS template landing is fully static — no API calls.
describe("LandingPage", () => {
  it("renders the template navigation, hero copy and CTAs", () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    // brand (header, mockup sidebar, footer) + nav links
    // nav links repeat in the footer, so match on all occurrences
    expect(screen.getAllByText("AquaSense").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Live demo")).toHaveLength(2);
    expect(screen.getAllByText("Analytics")).toHaveLength(2);
    expect(screen.getAllByText("Documentation")).toHaveLength(2);

    // hero copy + announcement banner
    expect(screen.getByText(/Every drop of water/)).toBeInTheDocument();
    expect(screen.getByText(/seven-day demand forecasting is live/)).toBeInTheDocument();
    expect(screen.getByText("See what's new")).toBeInTheDocument();

    // CTAs — the mobile drawer is closed until toggled, so these render once
    expect(screen.getByText("Get started")).toBeInTheDocument();
    expect(screen.getByText("View analytics")).toBeInTheDocument();
    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
    expect(screen.getByText("Open dashboard")).toBeInTheDocument();
  });

  it("opens and closes the mobile navigation drawer", () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    const toggle = screen.getByRole("button", { name: "Toggle menu" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    // drawer links are absent until the menu opens
    expect(screen.getAllByText("Open dashboard")).toHaveLength(1);

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    // header + drawer
    expect(screen.getAllByText("Open dashboard")).toHaveLength(2);
    expect(screen.getAllByText("AI Assistant")).toHaveLength(2);

    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.getAllByText("Open dashboard")).toHaveLength(1);
  });

  it("previews the dashboard with a self-contained mockup", () => {
    const view = render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    // the preview art is built in Tailwind, not loaded off a CDN
    expect(view.container.querySelectorAll("img")).toHaveLength(0);
    view.container.querySelectorAll("*").forEach((el) => {
      const src = el.getAttribute("src");
      expect(src === null || !/^https?:/i.test(src)).toBe(true);
    });

    // mockup surfaces the real sample aggregates
    expect(screen.getByText("Total consumed")).toBeInTheDocument();
    expect(screen.getByText("Wastage rate")).toBeInTheDocument();
    expect(screen.getByText("Active areas")).toBeInTheDocument();
    expect(screen.getByText("Leak events")).toBeInTheDocument();
  });

  it("lists the feature strip", () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );
    for (const title of [
      "Wastage detection",
      "Peak analysis",
      "Anomaly detection",
      "Demand forecasting",
    ]) {
      expect(screen.getByText(title)).toBeInTheDocument();
    }
  });

  it("renders the scroll-reveal statement and the electric brand mark", () => {
    const view = render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );

    // ScrollReveal splits the statement into animated .word spans
    const statement = view.container.querySelector(".scroll-reveal");
    expect(statement).toBeInTheDocument();
    expect(statement?.querySelectorAll(".word").length).toBeGreaterThan(0);
    expect((statement?.textContent ?? "").replace(/\s+/g, " ")).toContain(
      "350,400 hourly readings",
    );

    // ElectricLogo mounts in the nav as the brand mark
    expect(view.container.querySelector(".electric-logo")).toBeInTheDocument();
  });

  it("wires actions to real app routes", () => {
    const view = render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>,
    );
    const links = Array.from(view.container.querySelectorAll("a")).map((a) =>
      a.getAttribute("href"),
    );
    // header CTAs / nav / hero CTAs / feature cards all resolve to app routes
    expect(links).toContain("/");
    expect(links).toContain("/dashboard");
    expect(links).toContain("/areas");
    expect(links).toContain("/about");
    expect(links).toContain("/assistant");
    expect(links).toContain("/forecast");
    expect(links).toContain("/wastage");
    expect(links).toContain("/peak");
    expect(links).toContain("/anomalies");
  });
});
