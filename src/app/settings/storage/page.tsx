import { getStorageConfigStatus } from "@/server/storage/config";

export const dynamic = "force-dynamic";

export default async function StorageSettingsPage() {
  const status = await getStorageConfigStatus();

  return (
    <main className="app-shell">
      <section className="intro">
        <p className="eyebrow">设置 / 本地知识库目录</p>
        <h1>本地知识库目录配置</h1>
        <p>
          当前阶段只读取环境变量中的默认目录，并提供目录校验 API。页面暂不保存配置、
          不扫描 Markdown 文件，也不会写入、移动或删除用户文件。
        </p>
        <dl className="status-list" aria-label="当前目录配置状态">
          <div>
            <dt>配置状态</dt>
            <dd>{status.configured ? "已填写环境变量" : "未设置"}</dd>
          </div>
          <div>
            <dt>配置来源</dt>
            <dd>{status.source ?? "未设置"}</dd>
          </div>
          <div>
            <dt>校验结果</dt>
            <dd>{status.validation.message}</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
