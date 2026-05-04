import { constants } from "node:fs";
import { access, stat } from "node:fs/promises";
import path from "node:path";

export const KNOWLEDGE_BASE_ENV_KEYS = ["KNOWLEDGE_BASE_DIR", "VAULT_ROOT"] as const;

export type KnowledgeBaseEnvKey = (typeof KNOWLEDGE_BASE_ENV_KEYS)[number];

export type StorageValidationCode =
  | "ok"
  | "empty_path"
  | "not_found"
  | "not_directory"
  | "not_readable";

export type StorageValidationResult = {
  ok: boolean;
  code: StorageValidationCode;
  message: string;
  name: string | null;
};

export type StorageConfigStatus = {
  configured: boolean;
  source: KnowledgeBaseEnvKey | null;
  validation: StorageValidationResult;
};

export type ConfiguredKnowledgeBaseDirectory =
  | {
      configured: true;
      source: KnowledgeBaseEnvKey;
      rootPath: string;
      validation: StorageValidationResult & {
        ok: true;
      };
    }
  | {
      configured: boolean;
      source: KnowledgeBaseEnvKey | null;
      rootPath: null;
      validation: StorageValidationResult;
    };

export type KnowledgeBaseEnvironment = Partial<Record<KnowledgeBaseEnvKey, string | undefined>>;

export type StorageFileSystemAdapter = {
  stat: (inputPath: string) => Promise<DirectoryStats>;
  access: (inputPath: string, mode?: number) => Promise<void>;
};

type StorageConfigOptions = {
  env?: KnowledgeBaseEnvironment;
  fs?: StorageFileSystemAdapter;
};

type DirectoryStats = {
  isDirectory: () => boolean;
};

const defaultFileSystem: StorageFileSystemAdapter = {
  stat,
  access
};

export async function getStorageConfigStatus(
  options: StorageConfigOptions = {}
): Promise<StorageConfigStatus> {
  const configuredDirectory = await getConfiguredKnowledgeBaseDirectory(options);

  return {
    configured: configuredDirectory.configured,
    source: configuredDirectory.source,
    validation: configuredDirectory.validation
  };
}

export async function getConfiguredKnowledgeBaseDirectory(
  options: StorageConfigOptions = {}
): Promise<ConfiguredKnowledgeBaseDirectory> {
  const env = options.env ?? getProcessKnowledgeBaseEnvironment();
  const configuredPath = getConfiguredKnowledgeBasePath(env);
  const validation = await validateKnowledgeBaseDirectory(configuredPath.value, {
    fs: options.fs
  });

  if (configuredPath.value && configuredPath.source && validation.ok) {
    return {
      configured: true,
      source: configuredPath.source,
      rootPath: configuredPath.value,
      validation: validation as StorageValidationResult & {
        ok: true;
      }
    };
  }

  return {
    configured: configuredPath.value !== null,
    source: configuredPath.source,
    rootPath: null,
    validation
  };
}

export async function validateKnowledgeBaseDirectory(
  inputPath: string | null | undefined,
  options: Pick<StorageConfigOptions, "fs"> = {}
): Promise<StorageValidationResult> {
  const fs = options.fs ?? defaultFileSystem;
  const normalizedPath = normalizeInputPath(inputPath);

  if (!normalizedPath) {
    return createValidationResult("empty_path", null);
  }

  let stats: DirectoryStats;

  try {
    stats = await fs.stat(normalizedPath);
  } catch {
    return createValidationResult("not_found", getSafeDirectoryName(normalizedPath));
  }

  if (!stats.isDirectory()) {
    return createValidationResult("not_directory", getSafeDirectoryName(normalizedPath));
  }

  try {
    await fs.access(normalizedPath, constants.R_OK);
  } catch {
    return createValidationResult("not_readable", getSafeDirectoryName(normalizedPath));
  }

  return createValidationResult("ok", getSafeDirectoryName(normalizedPath));
}

function getProcessKnowledgeBaseEnvironment(): KnowledgeBaseEnvironment {
  return {
    KNOWLEDGE_BASE_DIR: process.env.KNOWLEDGE_BASE_DIR,
    VAULT_ROOT: process.env.VAULT_ROOT
  };
}

function getConfiguredKnowledgeBasePath(env: KnowledgeBaseEnvironment) {
  for (const source of KNOWLEDGE_BASE_ENV_KEYS) {
    const value = normalizeInputPath(env[source]);

    if (value) {
      return {
        source,
        value
      };
    }
  }

  return {
    source: null,
    value: null
  };
}

function normalizeInputPath(inputPath: string | null | undefined) {
  const trimmed = inputPath?.trim();

  return trimmed && trimmed.length > 0 ? trimmed : null;
}

function getSafeDirectoryName(inputPath: string) {
  return path.basename(path.resolve(inputPath)) || null;
}

function createValidationResult(
  code: StorageValidationCode,
  name: string | null
): StorageValidationResult {
  return {
    ok: code === "ok",
    code,
    message: getValidationMessage(code),
    name
  };
}

function getValidationMessage(code: StorageValidationCode) {
  switch (code) {
    case "ok":
      return "目录可读取。";
    case "empty_path":
      return "知识库目录路径不能为空。";
    case "not_found":
      return "目录不存在。";
    case "not_directory":
      return "路径必须指向目录。";
    case "not_readable":
      return "当前进程没有读取该目录的权限。";
  }
}
