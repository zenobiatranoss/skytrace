import { describe, expect, it } from "vitest";

import {
  haversineKm,
  metersToFeet,
  msToFeetPerMinute,
  msToKnots,
  normalizeHeading,
} from "./coordinates";

describe("unit conversions", () => {
  it("converts meters to feet", () => {
    expect(metersToFeet(304.8)).toBeCloseTo(1000, 3);
  });

  it("passes null through", () => {
    expect(metersToFeet(null)).toBeNull();
    expect(msToKnots(null)).toBeNull();
    expect(msToFeetPerMinute(null)).toBeNull();
  });

  it("converts m/s to knots", () => {
    expect(msToKnots(100)).toBeCloseTo(194.38, 1);
  });
});

describe("normalizeHeading", () => {
  it("wraps negative and out-of-range headings", () => {
    expect(normalizeHeading(-10)).toBe(350);
    expect(normalizeHeading(370)).toBe(10);
  });

  it("keeps null as null", () => {
    expect(normalizeHeading(null)).toBeNull();
  });
});

describe("haversineKm", () => {
  it("measures a known distance", () => {
    // paris (cdg) to london (heathrow) is roughly 350km
    const d = haversineKm(49.0097, 2.5479, 51.47, -0.4543);
    expect(d).toBeGreaterThan(330);
    expect(d).toBeLessThan(360);
  });

  it("is zero for the same point", () => {
    expect(haversineKm(10, 10, 10, 10)).toBeCloseTo(0, 5);
  });
});
