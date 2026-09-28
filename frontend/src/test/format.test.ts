import { describe, expect, it } from "vitest";

import { fmtDateLabel, fmtLiters, fmtNum, fmtPct, fmtTimestamp, secondsToClock, shortLabel } from "@/lib/format";

describe("fmtLiters", () => {
  it("renders large volumes compactly", () => {
    expect(fmtLiters(980_570)).toBe("980.6k L");
    expect(fmtLiters(13_010_601)).toBe("13.01M L");
    expect(fmtLiters(580_650)).toBe("580.6k L");
  });

  it("renders small volumes in litres", () => {
    expect(fmtLiters(42)).toBe("42 L");
    expect(fmtLiters(999)).toBe("999 L");
  });

  it("handles nullish / non-finite input", () => {
    expect(fmtLiters(null)).toBe("—");
    expect(fmtLiters(undefined)).toBe("—");
    expect(fmtLiters(Number.NaN)).toBe("—");
  });
});

describe("fmtNum / fmtPct", () => {
  it("formats counts with thousand separators", () => {
    expect(fmtNum(350_400)).toBe("350,400");
    expect(fmtNum(0)).toBe("0");
    expect(fmtNum(null)).toBe("—");
  });

  it("formats percentages", () => {
    expect(fmtPct(4.4582)).toBe("4.5%");
    expect(fmtPct(0.1234, 2)).toBe("0.12%");
    expect(fmtPct(undefined)).toBe("—");
  });
});

describe("date helpers", () => {
  it("parses ISO date labels", () => {
    expect(fmtDateLabel("2025-08-05T00:00:00")).toMatch(/aug/i);
  });

  it("falls back to raw input for garbage timestamps", () => {
    expect(shortLabel("not-a-date")).toBe("not-a-date");
    expect(fmtTimestamp("garbage")).toBe("garbage");
  });
});

describe("secondsToClock", () => {
  it("renders h/m/s clocks", () => {
    expect(secondsToClock(262)).toBe("4m 22s");
    expect(secondsToClock(90)).toBe("1m 30s");
    expect(secondsToClock(45)).toBe("45s");
    expect(secondsToClock(3725)).toBe("1h 2m 5s");
  });
});