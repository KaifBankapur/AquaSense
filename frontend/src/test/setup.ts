import "@testing-library/jest-dom";

// jsdom lacks these browser APIs used by the theme hook and Recharts.
if (typeof window !== "undefined") {
  if (!window.matchMedia) {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: (query: string) => ({
        // Honour the two queries the app actually branches on. The default is
        // "no reduced-motion preference", so the animated paths run in tests
        // rather than silently falling through to the reduced-motion branch.
        matches:
          /prefers-color-scheme:\s*light/.test(query) ||
          /prefers-reduced-motion:\s*no-preference/.test(query),
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

  if (!("ResizeObserver" in window)) {
    class ResizeObserverMock {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
    Object.defineProperty(window, "ResizeObserver", {
      writable: true,
      value: ResizeObserverMock,
    });
  }

  if (!Object.prototype.hasOwnProperty.call(SVGElement.prototype, "getBBox")) {
    (SVGElement.prototype as unknown as { getBBox: () => DOMRect }).getBBox = () =>
      ({ x: 0, y: 0, width: 0, height: 0 }) as DOMRect;
  }
}