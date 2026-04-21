import { useEffect, useMemo, useRef, useState, type ChangeEvent, type MouseEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { LoaderCircle, ScanSearch, Trash2, Upload, WandSparkles } from 'lucide-react'
import { EmptyStateCard, ErrorStateCard } from '@/components/settings-section'
import { PermissionButton, PermissionGate } from '@/components/permission-gate'
import { notesApi } from '@/lib/notes-api'
import type { JobRecord, NoteGenerateResult } from '@/types/notes'
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

function normalizeJobStatus(status: string | undefined) {
  if (status === 'queued' || status === 'pending') return 'queued'
  if (status === 'running') return 'running'
  if (status === 'completed') return 'completed'
  if (status === 'failed') return 'failed'
  return 'queued'
}

function getGeneratedCountFromJob(job: JobRecord | null | undefined, fallback: NoteGenerateResult | null) {
  const jobGeneratedIds = job?.result_json?.generated_note_ids
  if (Array.isArray(jobGeneratedIds)) return jobGeneratedIds.length
  return fallback?.generated_note_ids.length ?? 0
}

function getGenerateStatusMessage(job: JobRecord | null | undefined, fallback: NoteGenerateResult | null) {
  if (!fallback) return null

  const normalizedStatus = normalizeJobStatus(job?.status ?? fallback.status)
  const jobId = job?.id ?? fallback.job

  if (normalizedStatus === 'failed') {
    return {
      tone: 'error' as const,
      text: `任务 #${jobId} 生成失败${job?.error_message ? `：${job.error_message}` : '。'}`,
    }
  }

  if (normalizedStatus === 'completed') {
    const generatedCount = getGeneratedCountFromJob(job, fallback)
    return {
      tone: 'success' as const,
      text: `任务 #${jobId} 已完成，生成 ${generatedCount} 篇笔记。`,
    }
  }

  if (normalizedStatus === 'running') {
    return {
      tone: 'info' as const,
      text: `任务 #${jobId} 正在生成笔记，请稍候…`,
    }
  }

  return {
    tone: 'info' as const,
    text: `任务 #${jobId} 已创建，正在排队生成笔记…`,
  }
}

export function NotesGeneratePage() {
  const queryClient = useQueryClient()
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const [rootPath, setRootPath] = useState('.')
  const [uploadDirectory, setUploadDirectory] = useState('uploads/sources')
  const [noteDirectory, setNoteDirectory] = useState('notes/generated')
  const [fileTypeFilter, setFileTypeFilter] = useState<(typeof FILE_TYPE_OPTIONS)[number]['value']>('all')
  const [selectedAssetIds, setSelectedAssetIds] = useState<number[]>([])
  const [forceRegenerate, setForceRegenerate] = useState(false)
  const [syncToObsidian, setSyncToObsidian] = useState(false)
  const [activeGenerateJob, setActiveGenerateJob] = useState<NoteGenerateResult | null>(null)

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

  const jobsQuery = useQuery({
    queryKey: ['jobs'],
    queryFn: () => notesApi.listJobs(),
    enabled: isAdmin && activeGenerateJob !== null,
    refetchInterval: (query) => {
      const jobs = query.state.data as JobRecord[] | undefined
      const currentJob = jobs?.find((job) => job.id === activeGenerateJob?.job)
      const status = normalizeJobStatus(currentJob?.status ?? activeGenerateJob?.status)
      return status === 'completed' || status === 'failed' ? false : 1500
    },
  })

  const activeJobRecord = useMemo(
    () => jobsQuery.data?.find((job) => job.id === activeGenerateJob?.job) ?? null,
    [activeGenerateJob?.job, jobsQuery.data],
  )

  const generateStatus = useMemo(
    () => getGenerateStatusMessage(activeJobRecord, activeGenerateJob),
    [activeGenerateJob, activeJobRecord],
  )

  const selectedAssetIdSet = useMemo(() => new Set(selectedAssetIds), [selectedAssetIds])

  useEffect(() => {
    if (!activeGenerateJob) return

    const status = normalizeJobStatus(activeJobRecord?.status ?? activeGenerateJob.status)
    if (status === 'completed' || status === 'failed') {
      void queryClient.invalidateQueries({ queryKey: ['notes'] })
    }
  }, [activeGenerateJob, activeGenerateJob?.status, activeJobRecord?.status, queryClient])

  useEffect(() => {
    const assets = sourcesQuery.data
    if (!assets?.length) return

    const availableAssetIds = new Set(assets.map((asset) => asset.id))
    setSelectedAssetIds((current) => {
      const next = current.filter((assetId) => availableAssetIds.has(assetId))
      return next.length === current.length ? current : next
    })
  }, [sourcesQuery.data])

  const uploadMutation = useMutation({
    mutationFn: (file: File) => notesApi.uploadSource({ file, uploadDir: uploadDirectory }),
    onSuccess: (asset) => {
      void queryClient.invalidateQueries({ queryKey: ['sources'] })
      setSelectedAssetIds((current) => (current.includes(asset.id) ? current : [asset.id, ...current]))
      setFileTypeFilter('all')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    },
  })

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
    onSuccess: (result) => {
      setActiveGenerateJob(result)
      void Promise.all([
        queryClient.invalidateQueries({ queryKey: ['notes'] }),
        queryClient.invalidateQueries({ queryKey: ['jobs'] }),
      ])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (assetId: number) => notesApi.deleteSource(assetId),
    onSuccess: ({ id }) => {
      void queryClient.invalidateQueries({ queryKey: ['sources'] })
      setSelectedAssetIds((current) => current.filter((assetId) => assetId !== id))
    },
  })

  const toggleAsset = (assetId: number, checked: boolean) => {
    setSelectedAssetIds((current) => {
      if (checked) {
        return current.includes(assetId) ? current : [...current, assetId]
      }
      return current.filter((id) => id !== assetId)
    })
  }

  const handleDeleteAsset = (event: MouseEvent<HTMLButtonElement>, assetId: number) => {
    event.stopPropagation()
    deleteMutation.mutate(assetId)
  }

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    uploadMutation.mutate(file)
  }

  return (
    <div className="space-y-4">
      <section className="fabric-panel space-y-5">
        <PermissionGate allowed={isAdmin} reason="仅管理员可触发上传、扫描与生成">
          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,1.6fr)]">
            <section className="space-y-4">
              <div className="fabric-card space-y-4">
                <div>
                  <p className="text-sm font-semibold text-cloth-ink">直接上传来源文件</p>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-cloth-ink">上传目录</label>
                  <input value={uploadDirectory} onChange={(event) => setUploadDirectory(event.target.value)} className="fabric-input" disabled={!isAdmin || uploadMutation.isPending} />
                </div>
                <label className="fabric-upload-surface block">
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleFileChange}
                    disabled={!isAdmin || uploadMutation.isPending}
                    aria-label="上传来源文件"
                    className="fabric-file-input"
                  />
                </label>
                {uploadMutation.isPending ? (
                  <div className="flex items-center gap-2 text-sm text-cloth-muted">
                    <Upload className="h-4 w-4" />
                    上传中…
                  </div>
                ) : null}
              </div>

              <div className="fabric-card space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-cloth-ink">扫描目录</label>
                  <input value={rootPath} onChange={(event) => setRootPath(event.target.value)} className="fabric-input" disabled={!isAdmin} />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-cloth-ink">输出笔记目录</label>
                  <input value={noteDirectory} onChange={(event) => setNoteDirectory(event.target.value)} className="fabric-input" disabled={!isAdmin} />
                </div>
                <label className="fabric-switch-row">
                  <span>强制重生成已存在笔记</span>
                  <input type="checkbox" role="switch" checked={forceRegenerate} onChange={(event) => setForceRegenerate(event.target.checked)} disabled={!isAdmin} className="fabric-switch" />
                </label>
                <label className="fabric-switch-row">
                  <span>生成后同步到 Obsidian</span>
                  <input type="checkbox" role="switch" checked={syncToObsidian} onChange={(event) => setSyncToObsidian(event.target.checked)} disabled={!isAdmin} className="fabric-switch" />
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
                    {generateMutation.isPending ? '生成中...' : '开始生成'}
                  </PermissionButton>
                </div>
              </div>

              {(uploadMutation.isError || scanMutation.isError || generateMutation.isError || deleteMutation.isError) ? (
                <ErrorStateCard
                  title="操作失败"
                  description={String(uploadMutation.error?.message ?? scanMutation.error?.message ?? generateMutation.error?.message ?? deleteMutation.error?.message ?? '操作失败')}
                />
              ) : null}
              {uploadMutation.data ? (
                <div className="rounded-xl border border-cloth-success/40 bg-cloth-success/10 p-3 text-sm text-cloth-ink">
                  上传成功：资产 #{uploadMutation.data.id}
                </div>
              ) : null}
              {generateStatus ? (
                <div
                  className={`rounded-xl border p-3 text-sm ${
                    generateStatus.tone === 'success'
                      ? 'border-cloth-success/40 bg-cloth-success/10 text-cloth-ink'
                      : generateStatus.tone === 'error'
                        ? 'border-red-300 bg-red-50 text-red-700'
                        : 'border-cloth-accent/30 bg-cloth-panel/60 text-cloth-ink'
                  }`}
                >
                  {generateStatus.text}
                </div>
              ) : null}
            </section>

            <section className="fabric-card space-y-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-semibold text-cloth-ink">来源资产列表</p>
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
                    const selected = selectedAssetIdSet.has(asset.id)
                    const deleting = deleteMutation.isPending && deleteMutation.variables === asset.id
                    return (
                      <div key={asset.id} className={`rounded-xl border p-4 text-sm shadow-sm ${selected ? 'border-cloth-accent/60 bg-white/80' : 'border-cloth-line/70 bg-white/45'}`} data-selected={selected ? 'true' : 'false'}>
                        <div className="flex items-start gap-3">
                          <input
                            type="checkbox"
                            aria-label={asset.file_path}
                            checked={selected}
                            onChange={(event) => toggleAsset(asset.id, event.currentTarget.checked)}
                            disabled={!isAdmin || deleting}
                            className="fabric-checkbox mt-1"
                          />
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <p className="truncate font-semibold text-cloth-ink">{asset.file_path}</p>
                              <div className="flex items-center gap-2">
                                <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs uppercase tracking-[0.16em] text-cloth-muted">{asset.file_type}</span>
                                <PermissionButton
                                  allowed={isAdmin}
                                  className="fabric-btn"
                                  reason="仅管理员可删除来源资产"
                                  onClick={(event) => handleDeleteAsset(event, asset.id)}
                                  disabled={deleting}
                                >
                                  <Trash2 className="h-4 w-4" />
                                  {deleting ? '删除中...' : '删除'}
                                </PermissionButton>
                              </div>
                            </div>
                            <p className="mt-2 text-xs text-cloth-muted">资产 #{asset.id} · SHA {asset.checksum.slice(0, 12)}...</p>
                          </div>
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <EmptyStateCard title="暂无可用资产" description="请先上传或扫描文件。" />
                )}
              </div>
            </section>
          </div>
        </PermissionGate>

        {!isAdmin ? <div className="fabric-card text-sm text-cloth-muted">普通用户可访问此页，但生成能力保持禁用。</div> : null}
      </section>
    </div>
  )
}
