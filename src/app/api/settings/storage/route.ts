import { getStorageConfigStatus } from "@/server/storage/config";

export const runtime = "nodejs";

export async function GET() {
  return Response.json(await getStorageConfigStatus());
}
