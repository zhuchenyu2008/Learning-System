import { scanConfiguredMarkdownNotes } from "@/server/notes/scan";

export const runtime = "nodejs";

export async function GET() {
  const result = await scanConfiguredMarkdownNotes();
  const status = result.ok ? 200 : 503;

  return Response.json(result, { status });
}
