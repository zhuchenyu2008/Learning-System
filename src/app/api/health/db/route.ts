import { getDatabaseHealthReport } from "@/server/db/health";

export const runtime = "nodejs";

export async function GET() {
  const report = await getDatabaseHealthReport();
  const status = report.status === "ok" ? 200 : 503;

  return Response.json(report, { status });
}
