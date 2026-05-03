import { getHealthReport } from "@/server/health";

export const runtime = "nodejs";

export function GET() {
  return Response.json(getHealthReport());
}
