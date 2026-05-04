import { describe, expect, it } from "vitest";
import { getDatabaseHealthReport } from "./health";

const now = new Date("2026-05-04T00:00:00.000Z");
const sensitiveDatabaseUrl = "postgres://learning:super-secret@db.internal:5432/learning";

describe("getDatabaseHealthReport", () => {
  it("reports unavailable when DATABASE_URL is missing", async () => {
    const report = await getDatabaseHealthReport({
      databaseUrl: "",
      now,
      query: async () => {
        throw new Error("query should not run without DATABASE_URL");
      }
    });

    expect(report).toEqual({
      status: "unavailable",
      service: "learning-system",
      database: {
        status: "unavailable"
      },
      timestamp: "2026-05-04T00:00:00.000Z"
    });
  });

  it("reports ok when the injected query succeeds", async () => {
    let queryCount = 0;

    const report = await getDatabaseHealthReport({
      databaseUrl: sensitiveDatabaseUrl,
      now,
      query: async () => {
        queryCount += 1;
      }
    });

    expect(queryCount).toBe(1);
    expect(report.status).toBe("ok");
    expect(report.database.status).toBe("ok");
    expect(JSON.stringify(report)).not.toContain(sensitiveDatabaseUrl);
  });

  it("does not expose connection details or raw errors when the query fails", async () => {
    const report = await getDatabaseHealthReport({
      databaseUrl: sensitiveDatabaseUrl,
      now,
      query: async () => {
        const error = new Error(`could not connect to ${sensitiveDatabaseUrl}`);
        error.stack = `Error: could not connect\n    at C:\\private\\project\\db.ts:1:1`;
        throw Object.assign(error, {
          host: "db.internal",
          user: "learning",
          password: "super-secret"
        });
      }
    });
    const payload = JSON.stringify(report);

    expect(report.status).toBe("unavailable");
    expect(report.database.status).toBe("unavailable");
    expect(payload).not.toContain(sensitiveDatabaseUrl);
    expect(payload).not.toContain("super-secret");
    expect(payload).not.toContain("db.internal");
    expect(payload).not.toContain("C:\\private");
    expect(payload).not.toContain("stack");
  });
});
