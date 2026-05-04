import { describe, expect, it } from "vitest";
import {
  getStorageConfigStatus,
  validateKnowledgeBaseDirectory
} from "./config";

function createDirectoryStats() {
  return {
    isDirectory: () => true
  };
}

function createFileStats() {
  return {
    isDirectory: () => false
  };
}

describe("validateKnowledgeBaseDirectory", () => {
  it("accepts an existing readable directory without exposing an absolute path", async () => {
    const result = await validateKnowledgeBaseDirectory("D:\\private\\vault", {
      fs: {
        stat: async () => createDirectoryStats(),
        access: async () => undefined
      }
    });

    expect(result).toEqual({
      ok: true,
      code: "ok",
      message: "目录可读取。",
      name: "vault"
    });
    expect(JSON.stringify(result)).not.toContain("D:\\private");
  });

  it("rejects an empty path before touching the file system", async () => {
    let statCount = 0;
    const result = await validateKnowledgeBaseDirectory("  ", {
      fs: {
        stat: async () => {
          statCount += 1;
          return createDirectoryStats();
        },
        access: async () => undefined
      }
    });

    expect(statCount).toBe(0);
    expect(result).toMatchObject({
      ok: false,
      code: "empty_path",
      name: null
    });
  });

  it("rejects a path that does not exist", async () => {
    const result = await validateKnowledgeBaseDirectory("D:\\private\\missing-vault", {
      fs: {
        stat: async () => {
          throw new Error("missing");
        },
        access: async () => undefined
      }
    });

    expect(result).toMatchObject({
      ok: false,
      code: "not_found",
      name: "missing-vault"
    });
    expect(JSON.stringify(result)).not.toContain("D:\\private");
  });

  it("rejects a file path", async () => {
    const result = await validateKnowledgeBaseDirectory("D:\\private\\notes.md", {
      fs: {
        stat: async () => createFileStats(),
        access: async () => undefined
      }
    });

    expect(result).toMatchObject({
      ok: false,
      code: "not_directory",
      name: "notes.md"
    });
  });

  it("rejects a directory that cannot be read", async () => {
    const result = await validateKnowledgeBaseDirectory("D:\\private\\locked-vault", {
      fs: {
        stat: async () => createDirectoryStats(),
        access: async () => {
          throw new Error("permission denied");
        }
      }
    });

    expect(result).toMatchObject({
      ok: false,
      code: "not_readable",
      name: "locked-vault"
    });
    expect(JSON.stringify(result)).not.toContain("permission denied");
  });
});

describe("getStorageConfigStatus", () => {
  it("uses KNOWLEDGE_BASE_DIR before VAULT_ROOT", async () => {
    const status = await getStorageConfigStatus({
      env: {
        KNOWLEDGE_BASE_DIR: "D:\\private\\knowledge",
        VAULT_ROOT: "D:\\private\\vault"
      },
      fs: {
        stat: async () => createDirectoryStats(),
        access: async () => undefined
      }
    });

    expect(status.configured).toBe(true);
    expect(status.source).toBe("KNOWLEDGE_BASE_DIR");
    expect(status.validation.name).toBe("knowledge");
    expect(JSON.stringify(status)).not.toContain("D:\\private");
  });

  it("falls back to VAULT_ROOT when KNOWLEDGE_BASE_DIR is empty", async () => {
    const status = await getStorageConfigStatus({
      env: {
        KNOWLEDGE_BASE_DIR: "",
        VAULT_ROOT: "D:\\private\\vault"
      },
      fs: {
        stat: async () => createDirectoryStats(),
        access: async () => undefined
      }
    });

    expect(status.configured).toBe(true);
    expect(status.source).toBe("VAULT_ROOT");
    expect(status.validation.name).toBe("vault");
  });

  it("reports unconfigured when no environment path is present", async () => {
    const status = await getStorageConfigStatus({
      env: {},
      fs: {
        stat: async () => {
          throw new Error("stat should not run");
        },
        access: async () => undefined
      }
    });

    expect(status).toMatchObject({
      configured: false,
      source: null,
      validation: {
        ok: false,
        code: "empty_path",
        name: null
      }
    });
  });

  it("keeps configured true when an environment path exists but validation fails", async () => {
    const status = await getStorageConfigStatus({
      env: {
        KNOWLEDGE_BASE_DIR: "D:\\private\\missing"
      },
      fs: {
        stat: async () => {
          throw new Error("missing");
        },
        access: async () => undefined
      }
    });

    expect(status).toMatchObject({
      configured: true,
      source: "KNOWLEDGE_BASE_DIR",
      validation: {
        ok: false,
        code: "not_found",
        name: "missing"
      }
    });
  });
});
