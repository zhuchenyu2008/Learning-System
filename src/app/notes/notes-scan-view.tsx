"use client";

import { useEffect, useState } from "react";

type NoteSummary = {
  id: string;
  title: string;
  relativePath: string;
  extension: string;
  sizeBytes: number;
  updatedAt: string;
  depth: number;
};

type NotesResponse = {
  configured: boolean;
  ok: boolean;
  count: number;
  notes: NoteSummary[];
  truncated: boolean;
  error?: {
    message: string;
  };
};

type LoadState =
  | {
      status: "loading";
    }
  | {
      status: "ready";
      data: NotesResponse;
    }
  | {
      status: "error";
      message: string;
    };

export default function NotesScanView() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let active = true;

    async function loadNotes() {
      try {
        const response = await fetch("/api/notes", {
          cache: "no-store"
        });
        const data = (await response.json()) as NotesResponse;

        if (!active) {
          return;
        }

        if (!response.ok || !data.ok) {
          setState({
            status: "error",
            message: data.error?.message ?? "Markdown 文件扫描暂时不可用。"
          });
          return;
        }

        setState({
          status: "ready",
          data
        });
      } catch {
        if (active) {
          setState({
            status: "error",
            message: "无法连接 Markdown 文件扫描接口。"
          });
        }
      }
    }

    void loadNotes();

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="notes-shell">
      <section className="notes-header">
        <p className="eyebrow">笔记 / Markdown dry-run</p>
        <h1>Markdown 文件扫描</h1>
        <p>
          当前页面只展示已配置知识库目录中的 Markdown 文件元信息，不读取完整正文，
          不渲染 Markdown，也不会修改用户文件。
        </p>
      </section>

      {state.status === "loading" ? <NotesLoading /> : null}
      {state.status === "error" ? <NotesError message={state.message} /> : null}
      {state.status === "ready" ? <NotesList data={state.data} /> : null}
    </main>
  );
}

function NotesLoading() {
  return <section className="notes-panel">正在扫描 Markdown 文件...</section>;
}

function NotesError({ message }: { message: string }) {
  return (
    <section className="notes-panel notes-panel-error">
      <h2>扫描不可用</h2>
      <p>{message}</p>
    </section>
  );
}

function NotesList({ data }: { data: NotesResponse }) {
  if (data.count === 0) {
    return (
      <section className="notes-panel">
        <h2>暂无 Markdown 文件</h2>
        <p>当前已配置目录中没有发现 `.md` 或 `.markdown` 文件。</p>
      </section>
    );
  }

  return (
    <section className="notes-panel">
      <div className="notes-summary">
        <h2>发现 {data.count} 个 Markdown 文件</h2>
        {data.truncated ? <p>结果已达到本阶段扫描上限，列表已截断。</p> : null}
      </div>
      <div className="notes-table-wrap">
        <table className="notes-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>相对路径</th>
              <th>大小</th>
              <th>更新时间</th>
            </tr>
          </thead>
          <tbody>
            {data.notes.map((note) => (
              <tr key={note.id}>
                <td>{note.title}</td>
                <td>{note.relativePath}</td>
                <td>{formatBytes(note.sizeBytes)}</td>
                <td>{formatDate(note.updatedAt)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function formatBytes(sizeBytes: number) {
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }

  return `${(sizeBytes / 1024).toFixed(1)} KB`;
}

function formatDate(updatedAt: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(updatedAt));
}
