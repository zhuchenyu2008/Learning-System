import { describe, expect, it } from "vitest";
import { getHealthReport } from "./health";

describe("getHealthReport", () => {
  it("returns a safe health payload", () => {
    const report = getHealthReport(new Date("2026-05-03T00:00:00.000Z"));

    expect(report).toMatchObject({
      status: "ok",
      service: "learning-system",
      timestamp: "2026-05-03T00:00:00.000Z"
    });
    expect(report.uptime).toBeGreaterThanOrEqual(0);
    expect(["development", "test", "production", "unknown"]).toContain(report.environment);
    expect(Object.keys(report)).toEqual([
      "status",
      "service",
      "timestamp",
      "uptime",
      "environment"
    ]);
  });
});
