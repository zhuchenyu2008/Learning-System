import { getDatabaseUrl, pingDatabase } from "./client";

export type DatabaseHealthStatus = "ok" | "unavailable";

export type DatabaseHealthReport = {
  status: DatabaseHealthStatus;
  service: "learning-system";
  database: {
    status: DatabaseHealthStatus;
  };
  timestamp: string;
};

type DatabaseHealthOptions = {
  databaseUrl?: string | null;
  query?: () => Promise<unknown>;
  now?: Date;
};

export async function getDatabaseHealthReport(
  options: DatabaseHealthOptions = {}
): Promise<DatabaseHealthReport> {
  const databaseUrl =
    options.databaseUrl === undefined ? getDatabaseUrl() : normalizeDatabaseUrl(options.databaseUrl);
  const timestamp = (options.now ?? new Date()).toISOString();

  if (!databaseUrl) {
    return createDatabaseHealthReport("unavailable", timestamp);
  }

  try {
    await (options.query ?? pingDatabase)();

    return createDatabaseHealthReport("ok", timestamp);
  } catch {
    return createDatabaseHealthReport("unavailable", timestamp);
  }
}

function normalizeDatabaseUrl(databaseUrl: string | null) {
  const trimmed = databaseUrl?.trim();

  return trimmed && trimmed.length > 0 ? trimmed : null;
}

function createDatabaseHealthReport(status: DatabaseHealthStatus, timestamp: string) {
  return {
    status,
    service: "learning-system" as const,
    database: {
      status
    },
    timestamp
  };
}
