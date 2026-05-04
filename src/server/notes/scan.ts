import { createHash } from "node:crypto";
import { lstat, open, readdir } from "node:fs/promises";
import path from "node:path";
import {
  getConfiguredKnowledgeBaseDirectory,
  type KnowledgeBaseEnvironment,
  type StorageFileSystemAdapter
} from "../storage/config";

export const MARKDOWN_SCAN_DEFAULTS = {
  maxFiles: 1000,
  maxDepth: 10,
  titleReadBytes: 64 * 1024
} as const;

const SKIPPED_DIRECTORY_NAMES = new Set(["node_modules", ".git", ".next", "dist", "build"]);
const MARKDOWN_EXTENSIONS = new Set([".md", ".markdown"]);

export type MarkdownNoteSummary = {
  id: string;
  title: string;
  relativePath: string;
  extension: string;
  sizeBytes: number;
  updatedAt: string;
  depth: number;
};

export type MarkdownScanResponse = {
  configured: boolean;
  ok: boolean;
  count: number;
  notes: MarkdownNoteSummary[];
  truncated: boolean;
  limits: {
    maxFiles: number;
    maxDepth: number;
    titleReadBytes: number;
  };
  error?: {
    code: "storage_unavailable" | "scan_root_unavailable" | "root_symlink_not_allowed";
    message: string;
    storageCode?: string;
  };
};

type MarkdownScanOptions = MarkdownScanLimits & {
  fs?: MarkdownScanFileSystem;
};

type MarkdownScanLimits = {
  maxFiles?: number;
  maxDepth?: number;
  titleReadBytes?: number;
};

type ConfiguredMarkdownScanOptions = MarkdownScanOptions & {
  env?: KnowledgeBaseEnvironment;
  storageFs?: StorageFileSystemAdapter;
};

type MarkdownScanFileSystem = {
  lstat: (inputPath: string) => Promise<FileSystemStats>;
  readdir: (inputPath: string) => Promise<DirectoryEntry[]>;
  readFileHead: (inputPath: string, maxBytes: number) => Promise<Buffer>;
};

type FileSystemStats = {
  isFile: () => boolean;
  isDirectory: () => boolean;
  isSymbolicLink: () => boolean;
  size: number;
  mtime: Date;
};

type DirectoryEntry = {
  name: string;
  isDirectory: () => boolean;
  isFile: () => boolean;
  isSymbolicLink: () => boolean;
};

type TraversalState = {
  notes: MarkdownNoteSummary[];
  truncated: boolean;
};

const defaultScanFileSystem: MarkdownScanFileSystem = {
  lstat,
  readdir: async (inputPath) => readdir(inputPath, { withFileTypes: true }),
  readFileHead
};

export async function scanConfiguredMarkdownNotes(
  options: ConfiguredMarkdownScanOptions = {}
): Promise<MarkdownScanResponse> {
  const configuredDirectory = await getConfiguredKnowledgeBaseDirectory({
    env: options.env,
    fs: options.storageFs
  });

  if (!configuredDirectory.rootPath) {
    return createErrorResponse({
      configured: configuredDirectory.configured,
      code: "storage_unavailable",
      message: "知识库目录未配置或不可读取。",
      storageCode: configuredDirectory.validation.code,
      limits: getLimits(options)
    });
  }

  return scanMarkdownNotes(configuredDirectory.rootPath, options);
}

export async function scanMarkdownNotes(
  rootPath: string,
  options: MarkdownScanOptions = {}
): Promise<MarkdownScanResponse> {
  const limits = getLimits(options);
  const fs = options.fs ?? defaultScanFileSystem;
  const rootStats = await readRootStats(rootPath, fs);

  if (!rootStats) {
    return createErrorResponse({
      configured: true,
      code: "scan_root_unavailable",
      message: "知识库目录暂时无法读取。",
      limits
    });
  }

  if (rootStats.isSymbolicLink()) {
    return createErrorResponse({
      configured: true,
      code: "root_symlink_not_allowed",
      message: "默认不跟随软链接知识库根目录。",
      limits
    });
  }

  if (!rootStats.isDirectory()) {
    return createErrorResponse({
      configured: true,
      code: "scan_root_unavailable",
      message: "知识库根目录不可用于扫描。",
      limits
    });
  }

  const state: TraversalState = {
    notes: [],
    truncated: false
  };

  await scanDirectory({
    rootPath,
    currentPath: rootPath,
    relativeDir: "",
    depth: 0,
    limits,
    fs,
    state
  });

  return {
    configured: true,
    ok: true,
    count: state.notes.length,
    notes: state.notes,
    truncated: state.truncated,
    limits
  };
}

async function scanDirectory(input: {
  rootPath: string;
  currentPath: string;
  relativeDir: string;
  depth: number;
  limits: Required<MarkdownScanLimits>;
  fs: MarkdownScanFileSystem;
  state: TraversalState;
}) {
  if (input.state.truncated || input.depth > input.limits.maxDepth) {
    return;
  }

  let entries: DirectoryEntry[];

  try {
    entries = await input.fs.readdir(input.currentPath);
  } catch {
    return;
  }

  for (const entry of sortEntries(entries)) {
    if (input.state.truncated) {
      return;
    }

    if (entry.isSymbolicLink()) {
      continue;
    }

    if (entry.isDirectory()) {
      await scanChildDirectory(input, entry);
      continue;
    }

    if (!entry.isFile() || !isMarkdownFile(entry.name)) {
      continue;
    }

    if (input.state.notes.length >= input.limits.maxFiles) {
      input.state.truncated = true;
      return;
    }

    const relativePath = joinRelativePath(input.relativeDir, entry.name);
    const filePath = path.join(input.currentPath, entry.name);
    const fileStats = await readFileStats(filePath, input.fs);

    if (!fileStats?.isFile() || fileStats.isSymbolicLink()) {
      continue;
    }

    input.state.notes.push(
      await createNoteSummary({
        filePath,
        relativePath,
        stats: fileStats,
        fs: input.fs,
        titleReadBytes: input.limits.titleReadBytes
      })
    );
  }
}

async function scanChildDirectory(
  input: Parameters<typeof scanDirectory>[0],
  entry: DirectoryEntry
) {
  const directoryName = entry.name.toLowerCase();

  if (SKIPPED_DIRECTORY_NAMES.has(directoryName)) {
    return;
  }

  const childDepth = input.depth + 1;

  if (childDepth > input.limits.maxDepth) {
    return;
  }

  await scanDirectory({
    ...input,
    currentPath: path.join(input.currentPath, entry.name),
    relativeDir: joinRelativePath(input.relativeDir, entry.name),
    depth: childDepth
  });
}

async function createNoteSummary(input: {
  filePath: string;
  relativePath: string;
  stats: FileSystemStats;
  fs: MarkdownScanFileSystem;
  titleReadBytes: number;
}): Promise<MarkdownNoteSummary> {
  const extension = path.extname(input.relativePath).toLowerCase();
  const fallbackTitle = path.basename(input.relativePath, path.extname(input.relativePath));
  const title = await readMarkdownTitle({
    filePath: input.filePath,
    fallbackTitle,
    fs: input.fs,
    titleReadBytes: input.titleReadBytes
  });

  return {
    id: createNoteId(input.relativePath),
    title,
    relativePath: input.relativePath,
    extension,
    sizeBytes: input.stats.size,
    updatedAt: input.stats.mtime.toISOString(),
    depth: getRelativeDepth(input.relativePath)
  };
}

async function readMarkdownTitle(input: {
  filePath: string;
  fallbackTitle: string;
  fs: MarkdownScanFileSystem;
  titleReadBytes: number;
}) {
  try {
    const head = await input.fs.readFileHead(input.filePath, input.titleReadBytes);
    const title = extractFirstH1(head.toString("utf8"));

    return title || input.fallbackTitle;
  } catch {
    return input.fallbackTitle;
  }
}

function extractFirstH1(markdownHead: string) {
  const normalized = markdownHead.replace(/^\uFEFF/, "");
  const match = normalized.match(/^#\s+(.+?)\s*#*\s*$/m);

  return match?.[1]?.trim() || null;
}

async function readRootStats(rootPath: string, fs: MarkdownScanFileSystem) {
  try {
    return await fs.lstat(rootPath);
  } catch {
    return null;
  }
}

async function readFileStats(filePath: string, fs: MarkdownScanFileSystem) {
  try {
    return await fs.lstat(filePath);
  } catch {
    return null;
  }
}

async function readFileHead(filePath: string, maxBytes: number) {
  const handle = await open(filePath, "r");

  try {
    const buffer = Buffer.alloc(maxBytes);
    const { bytesRead } = await handle.read(buffer, 0, maxBytes, 0);

    return buffer.subarray(0, bytesRead);
  } finally {
    await handle.close();
  }
}

function sortEntries(entries: DirectoryEntry[]) {
  return [...entries].sort((first, second) =>
    first.name.localeCompare(second.name, "zh-CN", {
      sensitivity: "base"
    })
  );
}

function isMarkdownFile(fileName: string) {
  return MARKDOWN_EXTENSIONS.has(path.extname(fileName).toLowerCase());
}

function joinRelativePath(relativeDir: string, name: string) {
  return relativeDir ? `${relativeDir}/${name}` : name;
}

function getRelativeDepth(relativePath: string) {
  return relativePath.split("/").length - 1;
}

function createNoteId(relativePath: string) {
  return createHash("sha256").update(relativePath).digest("hex").slice(0, 16);
}

function getLimits(options: MarkdownScanOptions) {
  return {
    maxFiles: options.maxFiles ?? MARKDOWN_SCAN_DEFAULTS.maxFiles,
    maxDepth: options.maxDepth ?? MARKDOWN_SCAN_DEFAULTS.maxDepth,
    titleReadBytes: options.titleReadBytes ?? MARKDOWN_SCAN_DEFAULTS.titleReadBytes
  };
}

function createErrorResponse(input: {
  configured: boolean;
  code: NonNullable<MarkdownScanResponse["error"]>["code"];
  message: string;
  storageCode?: string;
  limits: MarkdownScanResponse["limits"];
}): MarkdownScanResponse {
  return {
    configured: input.configured,
    ok: false,
    count: 0,
    notes: [],
    truncated: false,
    limits: input.limits,
    error: {
      code: input.code,
      message: input.message,
      storageCode: input.storageCode
    }
  };
}
