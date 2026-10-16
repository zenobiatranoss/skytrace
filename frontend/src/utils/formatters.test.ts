import { describe, expect, it } from "vitest";

import {
  formatAge,
  formatAltitude,
  formatCoords,
  formatHeading,
  formatVerticalRate,
  orUnavailable,
  UNAVAILABLE,
} from "./formatters";

describe("formatAltitude", () => {
  it("renders feet with a thousands separator", () => {
    expect(formatAltitude(11582.4)).toBe("38,000 ft");
  });

  it("shows a dash when missing", () => {
    expect(formatAltitude(null)).toBe(UNAVAILABLE);
  });
});

describe("formatVerticalRate", () => {
  it("adds a plus sign for climbs", () => {
    expect(formatVerticalRate(5)).toMatch(/^\+/);
  });

  it("does not add a sign for descents", () => {
    expect(formatVerticalRate(-5)).toMatch(/^-/);
  });
});

describe("formatCoords", () => {
  it("labels hemispheres", () => {
    expect(formatCoords(54.2975, 10.928)).toBe("54.2975°N, 10.9280°E");
    expect(formatCoords(-33.9, -70.6)).toBe("33.9000°S, 70.6000°W");
  });
});

describe("formatHeading", () => {
  it("rounds to whole degrees", () => {
    expect(formatHeading(218.89)).toBe("219°");
    expect(formatHeading(null)).toBe(UNAVAILABLE);
  });
});

describe("formatAge", () => {
  it("buckets seconds into readable ages", () => {
    expect(formatAge(2)).toBe("just now");
    expect(formatAge(30)).toBe("30s ago");
    expect(formatAge(120)).toBe("2m ago");
    expect(formatAge(7200)).toBe("2h ago");
  });
});

describe("orUnavailable", () => {
  it("falls back for empty strings", () => {
    expect(orUnavailable("  ")).toBe(UNAVAILABLE);
    expect(orUnavailable("BAW123")).toBe("BAW123");
    expect(orUnavailable(null)).toBe(UNAVAILABLE);
  });
});
