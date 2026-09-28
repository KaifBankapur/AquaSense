import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { StatCard } from "@/components/StatCard";
import { PageHeader } from "@/components/PageHeader";
import { App } from "@/App";
import { AppShell } from "@/layouts/AppShell";

// Default fetch stub for any component that calls the API on mount.
// Returning a non-ok response keeps DataFetch states deterministic.
beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      return new Response("not found", { status: 404, statusText: "Not Found" });
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
});

describe("StatCard", () => {
  it("renders label, value, unit and hint", () => {
    render(<StatCard label="Total consumed" value="13.01M" unit="L" hint="over 12 months" icon="droplets" />);
    expect(screen.getByText("Total consumed")).toBeInTheDocument();
    expect(screen.getByText("13.01M")).toBeInTheDocument();
    expect(screen.getByText("L")).toBeInTheDocument();
    expect(screen.getByText("over 12 months")).toBeInTheDocument();
  });

  it("renders a dash for a missing value", () => {
    // Scoped to this render: a bare getByText("—") also matches the em-dashes
    // inside Hero's FlipText when another test file's DOM is still mounted.
    const { container } = render(<StatCard label="Peak hour" value="—" />);
    expect(container).toHaveTextContent("—");
  });
});

describe("PageHeader", () => {
  it("renders title and description", () => {
    render(<PageHeader title="Wastage" description="Leak analysis" />);
    expect(screen.getByText("Wastage")).toBeInTheDocument();
    expect(screen.getByText("Leak analysis")).toBeInTheDocument();
  });
});

describe("App shell", () => {
  it("renders the sidebar navigation", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AppShell />
      </MemoryRouter>,
    );
    expect(screen.getByText("AquaSense")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Wastage" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "AI Assistant" })).toBeInTheDocument();
  });

  it("routes /assistant to the AquaAI page", async () => {
    render(
      <MemoryRouter initialEntries={["/assistant"]}>
        <App />
      </MemoryRouter>,
    );
    expect(await screen.findByText("AquaAI Assistant")).toBeInTheDocument();
    expect(screen.getAllByText(/local analytics mode/).length).toBeGreaterThan(0);
  });
});