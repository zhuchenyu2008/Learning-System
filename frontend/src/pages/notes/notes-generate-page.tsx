import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LoaderCircle, ScanSearch, WandSparkles } from 'lucide-react'
import { EmptyStateCard, ErrorStateCard } from '@/components/settings-section'
import { PermissionButton, PermissionGate } from '@/components/permission-gate'
import { notesApi } from '@/lib/notes-api'
import { useAuthStore } from '@/stores/auth-store'

const FILE_TYPE_OPTIONS = [
  { label: '全部类型', value: 'all' },
  { label: '音频', value: 'audio' },
  { label: '视频', value: 'video' },
  { label: '图片', value: 'image' },
  { label: '文本', value: 'text' },
  { label: 'Markdown', value: 'markdown' },
  { label: 'PDF', value: 'pdf' },
  { label: '其他', value: 'other' },
] as const

export function NotesGeneratePage() {
  const queryClient = useQueryClient()
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')
  const [rootPath, setRootPath] = useState('.')
  const [noteDirectory, setNoteDirectory] = useState('notes/generated')
  const [fileTypeFilter, setFileTypeFilter] = useState<(typeof FILE_TYPE_OPTIONS)[number]['value']>('all')
  const [selectedAssetIds, setSelectedAssetIds] = useState<number[]>([])
  const [forceRegenerate, setForceRegenerate] = useState(false)
  const [syncToObsidian, setSyncToObsidian] = useState(false)

  const sourcesQuery = useQuery({
    queryKey: ['sources'],
    queryFn: () => notesApi.listSources(),
    enabled: isAdmin,
  })

  const filteredAssets = useMemo(() => {
    const assets = sourcesQuery.data ?? []
    if (fileTypeFilter === 'all') return assets
    return assets.filter((asset) => asset.file_type === fileTypeFilter)
  }, [fileTypeFilter, sourcesQuery.data])

  const scanMutation = useMutation({
    mutationFn: () => notesApi.scanSources({ root_path: rootPath, recursive: true, include_hidden: false }),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ['sources'] })
      setSelectedAssetIds(result.assets.map((asset) => asset.id))
    },
  })

  const generateMutation = useMutation({
    mutationFn: () =>
      notesApi.generateNotes({
        source_asset_ids: selectedAssetIds,
        note_directory: noteDirectory,
        force_regenerate: forceRegenerate,
        sync_to_obsidian: syncToObsidian,
      }),
    onSuccess: () => {
      void Promise.all([
        queryClient.invalidateQueries({ queryKey: ['notes'] }),
        queryClient.invalidateQueries({ queryKey: ['jobs'] }),
      ])
    },
  })

  const toggleAsset = (assetId: number) => {
    setSelectedAssetIds((current) =>
      current.includes(assetId) ? current.filter((id) => id !== assetId) : [...current, assetId],
    )
  }

  return (
    <div className="space-y-4">
      <section className="fabric-panel space-y-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cloth-accent">Notes Generation</p>
          <h1 className="font-serif text-3xl text-cloth-ink">笔记生成</h1>
          <p className="mt-2 max-w-3xl text-sm text-cloth-muted">先扫描工作目录中的来源资产，再选择文件并触发后端现有生成 API。</p>
        </div>

        <PermissionGate allowed={isAdmin} reason="仅管理员可触发扫描与生成">
          <div className="grid gap-4 xl:grid-cols-[1.1fr_1.6fr]">
            <section className="fabric-card space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-cloth-ink">扫描目录</label>
                <input value={rootPath} onChange={(event) => setRootPath(event.target.value)} className="fabric-input" disabled={!isAdmin} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-cloth-ink">输出笔记目录</label>
                <input value={noteDirectory} onChange={(event) => setNoteDirectory(event.target.value)} className="fabric-input" disabled={!isAdmin} />
              </div>
              <label className="flex items-center gap-3 text-sm text-cloth-ink">
                <input type="checkbox" checked={forceRegenerate} onChange={(event) => setForceRegenerate(event.target.checked)} disabled={!isAdmin} />
                强制重生成已存在笔记
              </label>
              <label className="flex items-center gap-3 text-sm text-cloth-ink">
                <input type="checkbox" checked={syncToObsidian} onChange={(event) => setSyncToObsidian(event.target.checked)} disabled={!isAdmin} />
                生成后同步到 Obsidian
              </label>
              <div className="flex flex-wrap gap-3">
                <PermissionButton
                  allowed={isAdmin}
                  className="fabric-btn-primary"
                  reason="仅管理员可扫描工作目录"
                  onClick={() => scanMutation.mutate()}
                >
                  <ScanSearch className="h-4 w-4" />
                  {scanMutation.isPending ? '扫描中...' : '扫描工作目录'}
                </PermissionButton>
                <PermissionButton
                  allowed={isAdmin && selectedAssetIds.length > 0}
                  className="fabric-btn-primary"
                  reason={selectedAssetIds.length ? '仅管理员可触发笔记生成' : '请至少选择一个来源资产'}
                  onClick={() => generateMutation.mutate()}
                >
                  <WandSparkles className="h-4 w-4" />
                  {generateMutation.isPending ? '生成中...' : '触发笔记生成'}
                </PermissionButton>
              </div>
              {(scanMutation.isError || generateMutation.isError) ? (
                <ErrorStateCard title="操作失败" description={String(scanMutation.error?.message ?? generateMutation.error?.message ?? '操作失败')} />
              ) : null}
              {generateMutation.data ? (
                <div className="rounded-xl border border-cloth-success/40 bg-cloth-success/10 p-3 text-sm text-cloth-ink">
                  已创建任务 #{generateMutation.data.job}，生成 {generateMutation.data.generated_note_ids.length} 篇笔记。
                </div>
              ) : null}
            </section>

            <section className="fabric-card space-y-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-semibold text-cloth-ink">来源资产列表</p>
                  <p className="text-sm text-cloth-muted">支持按文件类型筛选后批量选择。</p>
                </div>
                <select value={fileTypeFilter} onChange={(event) => setFileTypeFilter(event.target.value as (typeof FILE_TYPE_OPTIONS)[number]['value'])} className="fabric-input max-w-[180px]" disabled={!isAdmin}>
                  {FILE_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>

              <div className="max-h-[540px] space-y-3 overflow-auto pr-1 scrollbar-thin">
                {sourcesQuery.isLoading ? (
                  <div className="flex items-center gap-2 rounded-xl border border-cloth-line/70 bg-white/50 p-4 text-sm text-cloth-muted">
                    <LoaderCircle className="h-4 w-4 animate-spin" />
                    正在加载来源资产...
                  </div>
                ) : filteredAssets.length ? (
                  filteredAssets.map((asset) => {
                    const selected = selectedAssetIds.includes(asset.id)
                    return (
                      <label key={asset.id} className={`block rounded-xl border p-4 text-sm shadow-sm ${selected ? 'border-cloth-accent/60 bg-white/80' : 'border-cloth-line/70 bg-white/45'}`}>
                        <div className="flex items-start gap-3">
                          <input type="checkbox" checked={selected} onChange={() => toggleAsset(asset.id)} disabled={!isAdmin} className="mt-1" />
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <p className="truncate font-semibold text-cloth-ink">{asset.file_path}</p>
                              <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs uppercase tracking-[0.16em] text-cloth-muted">{asset.file_type}</span>
                            </div>
                            <p className="mt-2 text-xs text-cloth-muted">资产 #{asset.id} · SHA {asset.checksum.slice(0, 12)}...</p>
                          </div>
                        </div>
                      </label>
                    )
                  })
                ) : (
                  <EmptyStateCard title="暂无可用资产" description="请先扫描工作目录，或确认来源目录中存在可处理文件。" />
                )}
              </div>
            </section>
          </div>
        </PermissionGate>

        {!isAdmin ? <div className="fabric-card text-sm text-cloth-muted">普通用户可访问此页但所有生成能力保持禁用。</div> : null}
      </section>
    </div>
  )
}
