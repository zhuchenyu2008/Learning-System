import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import {
  MARKDOWN_SCAN_DEFAULTS,
  scanConfiguredMarkdownNotes,
  scanMarkdownNotes
} from "./scan";

const tempRoots: string[] = [];
const fixedDate = new Date("2026-05-04T00:00:00.000Z");
const customMaxFiles = 2;

async function createTempRoot() {
  const root = await mkdtemp(path.join(os.tmpdir(), "learning-system-notes-"));
  tempRoots.push(root);

  return root;
}

async function writeVaultFile(root: string, relativePath: string, content: string) {
  const filePath = path.join(root, ...relativePath.split("/"));
  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, content, "utf8");
}

afterEach(async () => {
  await Promise.all(tempRoots.splice(0).map((root) => rm(root, { recursive: true, force: true })));
});

describe("scanMarkdownNotes", () => {
  it("scans .md files and extracts a first-level heading title", async () => {
    const root = await createTempRoot();
    await writeVaultFile(root, "math/algebra.md", "# 代数基础\n\n正文不应返回。");

    const result = await scanMarkdownNotes(root);

    expect(result.ok).toBe(true);
    expect(result.count).toBe(1);
    expect(result.notes[0]).toMatchObject({
      title: "代数基础",
      relativePath: "math/algebra.md",
      extension: ".md",
      depth: 1
    });
    expect(result.notes[0].sizeBytes).toBeGreaterThan(0);
    expect(result.notes[0].updatedAt).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(JSON.stringify(result)).not.toContain(root);
    expect(JSON.stringify(result)).not.toContain("正文不应返回");
  });

  it("supports .markdown files case-insensitively", async () => {
    const root = await createTempRoot();
    await writeVaultFile(root, "Physics.MARKDOWN", "# 物理笔记\n");

    const result = await scanMarkdownNotes(root);

    expect(result.count).toBe(1);
    expect(result.notes[0]).toMatchObject({
      title: "物理笔记",
      relativePath: "Physics.MARKDOWN",
      extension: ".markdown"
    });
  });

  it("skips non-Markdown files", async () => {
    const root = await createTempRoot();
    await writeVaultFile(root, "note.md", "# 可见\n");
    await writeVaultFile(root, "image.png", "# 不可见\n");
    await writeVaultFile(root, "plain.txt", "# 不可见\n");

    const result = await scanMarkdownNotes(root);

    expect(result.count).toBe(1);
    expect(result.notes.map((note) => note.relativePath)).toEqual(["note.md"]);
  });

  it("skips node_modules, .git and .next directories", async () => {
    const root = await createTempRoot();
    await writeVaultFile(root, "visible.md", "# 可见\n");
    await writeVaultFile(root, "node_modules/package/hidden.md", "# 跳过\n");
    await writeVaultFile(root, ".git/hidden.md", "# 跳过\n");
    await writeVaultFile(root, ".next/hidden.md", "# 跳过\n");

    const result = await scanMarkdownNotes(root);

    expect(result.count).toBe(1);
    expect(result.notes[0].relativePath).toBe("visible.md");
    expect(JSON.stringify(result)).not.toContain("hidden.md");
  });

  it("uses the file name when a Markdown file has no first-level heading", async () => {
    const root = await createTempRoot();
    await writeVaultFile(root, "history/world.md", "## 二级标题\n正文");

    const result = await scanMarkdownNotes(root);

    expect(result.notes[0]).toMatchObject({
      title: "world",
      relativePath: "history/world.md"
    });
  });

  it("returns a clear truncated result after the maximum file count", async () => {
    const root = await createTempRoot();
    await writeVaultFile(root, "a.md", "# A\n");
    await writeVaultFile(root, "b.md", "# B\n");
    await writeVaultFile(root, "c.md", "# C\n");

    const result = await scanMarkdownNotes(root, { maxFiles: customMaxFiles });

    expect(result.ok).toBe(true);
    expect(result.count).toBe(customMaxFiles);
    expect(result.truncated).toBe(true);
    expect(result.limits.maxFiles).toBe(customMaxFiles);
    expect(result.notes.map((note) => note.relativePath)).toEqual(["a.md", "b.md"]);
  });

  it("does not follow symbolic link entries by default", async () => {
    const root = "D:\\vault";
    const result = await scanMarkdownNotes(root, {
      fs: {
        lstat: async (inputPath) => {
          if (inputPath === root) {
            return createStats("directory");
          }

          return createStats("file");
        },
        readdir: async () => [
          createEntry("real.md", "file"),
          createEntry("linked.md", "symlink")
        ],
        readFileHead: async (inputPath) => {
          if (inputPath.includes("linked.md")) {
            throw new Error("symlink should not be read");
          }

          return Buffer.from("# Real\n");
        }
      }
    });

    expect(result.count).toBe(1);
    expect(result.notes[0].relativePath).toBe("real.md");
    expect(JSON.stringify(result)).not.toContain("linked.md");
  });

  it("only requests the configured title-read byte limit", async () => {
    const root = "D:\\vault";
    let requestedBytes = 0;

    const result = await scanMarkdownNotes(root, {
      titleReadBytes: 12,
      fs: {
        lstat: async (inputPath) =>
          inputPath === root ? createStats("directory") : createStats("file", 1024),
        readdir: async () => [createEntry("large.md", "file")],
        readFileHead: async (_inputPath, maxBytes) => {
          requestedBytes = maxBytes;

          return Buffer.from("# Large\nmore text");
        }
      }
    });

    expect(requestedBytes).toBe(12);
    expect(result.notes[0].title).toBe("Large");
  });
});

describe("scanConfiguredMarkdownNotes", () => {
  it("returns a safe error when the knowledge base directory is not configured", async () => {
    const result = await scanConfiguredMarkdownNotes({
      env: {},
      storageFs: {
        stat: async () => {
          throw new Error("storage stat should not run");
        },
        access: async () => undefined
      }
    });

    expect(result.configured).toBe(false);
    expect(result.ok).toBe(false);
    expect(result.count).toBe(0);
    expect(result.notes).toEqual([]);
    expect(result.truncated).toBe(false);
    expect(result.limits).toEqual(MARKDOWN_SCAN_DEFAULTS);
    expect(result.error).toMatchObject({
      code: "storage_unavailable",
      storageCode: "empty_path"
    });
  });

  it("scans only the configured and validated knowledge base root", async () => {
    const root = await createTempRoot();
    await writeVaultFile(root, "configured.md", "# 已配置目录\n");

    const result = await scanConfiguredMarkdownNotes({
      env: {
        KNOWLEDGE_BASE_DIR: root
      }
    });

    expect(result.ok).toBe(true);
    expect(result.count).toBe(1);
    expect(result.notes[0].title).toBe("已配置目录");
    expect(JSON.stringify(result)).not.toContain(root);
  });
});

function createStats(kind: "directory" | "file" | "symlink", size = 16) {
  return {
    isFile: () => kind === "file",
    isDirectory: () => kind === "directory",
    isSymbolicLink: () => kind === "symlink",
    size,
    mtime: fixedDate
  };
}

function createEntry(name: string, kind: "directory" | "file" | "symlink") {
  return {
    name,
    isFile: () => kind === "file",
    isDirectory: () => kind === "directory",
    isSymbolicLink: () => kind === "symlink"
  };
}
