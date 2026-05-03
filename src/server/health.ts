export type HealthStatus = "ok";

export type HealthEnvironment = "development" | "test" | "production" | "unknown";

export type HealthReport = {
  status: HealthStatus;
  service: "learning-system";
  timestamp: string;
  uptime: number;
  environment: HealthEnvironment;
};

export function getHealthReport(now = new Date()): HealthReport {
  return {
    status: "ok",
    service: "learning-system",
    timestamp: now.toISOString(),
    uptime: getProcessUptime(),
    environment: getSafeEnvironment()
  };
}

function getProcessUptime() {
  return Math.max(0, Number(process.uptime().toFixed(3)));
}

function getSafeEnvironment(): HealthEnvironment {
  if (process.env.NODE_ENV === "development") {
    return "development";
  }

  if (process.env.NODE_ENV === "test") {
    return "test";
  }

  if (process.env.NODE_ENV === "production") {
    return "production";
  }

  return "unknown";
}
