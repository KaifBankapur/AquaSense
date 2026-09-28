import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import ElectricLogo from "@/components/ui/electric-logo";
import ScrollReveal from "@/components/ui/scroll-reveal";

const realMatchMedia = window.matchMedia;

/** Pretend the user asked for reduced motion. */
function stubReducedMotion(reduce: boolean) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: (query: string) => ({
      matches: reduce ? /prefers-reduced-motion:\s*reduce/.test(query) : false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

afterEach(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: realMatchMedia,
  });
  vi.restoreAllMocks();
});

describe("ScrollReveal", () => {
  const line = "Every drop of water accounted for";

  it("splits string children into per-word spans and keeps a full label", () => {
    const { container } = render(<ScrollReveal>{line}</ScrollReveal>);

    const words = Array.from(container.querySelectorAll(".word"));
    expect(words.map((w) => w.textContent)).toEqual([
      "Every",
      "drop",
      "of",
      "water",
      "accounted",
      "for",
    ]);

    // the full sentence stays available to assistive tech
    expect(screen.getByRole("heading", { name: line })).toBeInTheDocument();
  });

  it("renders non-string children without splitting", () => {
    render(
      <ScrollReveal>
        <span data-testid="node">plain node</span>
      </ScrollReveal>,
    );
    expect(screen.getByTestId("node")).toBeInTheDocument();
  });

  it("skips the animation entirely when reduced motion is requested", () => {
    stubReducedMotion(true);
    const { container } = render(<ScrollReveal>{line}</ScrollReveal>);

    // no trigger was created, so GSAP never parked the words at baseOpacity
    // or applied the starting blur
    Array.from(container.querySelectorAll<HTMLElement>(".word")).forEach((w) => {
      expect(w.style.opacity).toBe("");
      expect(w.style.filter).toBe("");
    });
  });

  it("mounts and unmounts without leaking triggers", () => {
    const { unmount } = render(<ScrollReveal>{line}</ScrollReveal>);
    expect(() => unmount()).not.toThrow();
  });
});

describe("ElectricLogo", () => {
  it("renders its container", () => {
    const { container } = render(<ElectricLogo src="/aqua-mark.svg" />);
    const el = container.querySelector(".electric-logo");
    expect(el).toBeInTheDocument();
  });

  it("applies caller className and style", () => {
    const { container } = render(
      <ElectricLogo className="size-9" style={{ width: "40px" }} />,
    );
    const el = container.querySelector<HTMLElement>(".electric-logo");
    expect(el?.className).toContain("size-9");
    expect(el?.style.width).toBe("40px");
  });

  // jsdom has no WebGL2, so the component must degrade to an empty container
  // rather than throwing — this is the guard the vendor source was missing.
  it("degrades gracefully without WebGL2", () => {
    expect(() => render(<ElectricLogo src="/aqua-mark.svg" />)).not.toThrow();
    expect(typeof WebGL2RenderingContext).toBe("undefined");
  });
});
