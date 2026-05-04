import { validateKnowledgeBaseDirectory } from "@/server/storage/config";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  const inputPath = typeof body?.path === "string" ? body.path : "";
  const result = await validateKnowledgeBaseDirectory(inputPath);
  const status = result.ok ? 200 : 400;

  return Response.json(result, { status });
}
