import { useMutation } from '@tanstack/react-query'
import { ChangeEvent, useState } from 'react'
import { Download, Upload } from 'lucide-react'
import { ApiError } from '@/lib/api-client'
import { settingsApi } from '@/lib/settings-api'
import { PermissionButton } from '@/components/permission-gate'
import { PagePlaceholder } from '@/components/page-placeholder'
import { EmptyStateCard, ReadonlyNotice, SectionStatus, SettingsSection } from '@/components/settings-section'
import { useAuthStore } from '@/stores/auth-store'

export function SettingsImportExportPage() {
  const isAdmin = useAuthStore((state) => state.user?.role === 'admin')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [messageTone, setMessageTone] = useState<'default' | 'success' | 'warning' | 'danger'>('default')

  const exportMutation = useMutation({
    mutationFn: () => settingsApi.exportDatabase(),
    onSuccess: (result) => {
      setMessage(result.path || result.filename || result.message || '数据库导出请求已提交。')
      setMessageTone('success')
    },
    onError: (error) => {
      setMessage(error instanceof ApiError ? error.message : '数据库导出失败。')
      setMessageTone('danger')
    },
  })

  const importMutation = useMutation({
    mutationFn: () => {
      const formData = new FormData()
      if (!selectedFile) {
        throw new Error('请先选择导入文件。')
      }
      formData.append('file', selectedFile)
      return settingsApi.importDatabase(formData)
    },
    onSuccess: (result) => {
      setMessage(result.message || result.status || '数据库导入请求已提交。')
      setMessageTone('success')
    },
    onError: (error) => {
      setMessage(error instanceof ApiError ? error.message : error instanceof Error ? error.message : '数据库导入失败。')
      setMessageTone('danger')
    },
  })

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSelectedFile(event.target.files?.[0] ?? null)
  }

  return (
    <PagePlaceholder
      title="导入导出"
      description="管理员可触发数据库导出与导入恢复。接口失败时会直接显示真实状态。"
      className="space-y-4"
      actions={
        <>
          <PermissionButton
            allowed={isAdmin}
            reason="仅管理员可导出数据库"
            onClick={() => exportMutation.mutate()}
            disabled={exportMutation.isPending}
          >
            <Download className="h-4 w-4" />
            {exportMutation.isPending ? '导出中…' : '导出数据库'}
          </PermissionButton>
          <PermissionButton
            allowed={isAdmin}
            reason="仅管理员可导入数据库"
            className="fabric-btn-primary"
            onClick={() => importMutation.mutate()}
            disabled={importMutation.isPending || !selectedFile}
          >
            <Upload className="h-4 w-4" />
            {importMutation.isPending ? '导入中…' : '导入数据库'}
          </PermissionButton>
        </>
      }
    >
      <ReadonlyNotice isAdmin={isAdmin} reason="普通用户仅可查看导入导出说明与表单结构，导入/导出操作保持禁用。" />
      {message ? <div className="md:col-span-2 xl:col-span-3"><SectionStatus status={message} tone={messageTone} /></div> : null}

      <SettingsSection title="数据库导出" description="导出数据库快照与配置索引。" className="md:col-span-2 xl:col-span-2">
        <div className="space-y-3 text-sm text-cloth-muted">
          <p>推荐在低峰期执行导出，并将导出包与工作目录文件一同备份。</p>
          <ul className="list-disc space-y-1 pl-5">
            <li>导出行为由 `/admin/database/export` 承载。</li>
            <li>前端仅显示接口返回的路径/消息，不伪造下载成功。</li>
            <li>若后端改为异步任务，可在“任务与调度”页查看 job 状态。</li>
          </ul>
        </div>
      </SettingsSection>

      <SettingsSection title="数据库导入" description="上传导出包并触发恢复或合并。" className="md:col-span-2 xl:col-span-1">
        <div className="space-y-3">
          <label className="fabric-upload-surface block">
            <input type="file" onChange={handleFileChange} disabled={!isAdmin} className="fabric-file-input" />
          </label>
          <div className="rounded-xl border border-dashed border-cloth-line/80 bg-white/35 p-4 text-sm text-cloth-muted">
            {selectedFile ? `已选择：${selectedFile.name}` : '请选择数据库导入包。'}
          </div>
        </div>
      </SettingsSection>

      <div className="md:col-span-2 xl:col-span-3">
        <EmptyStateCard title="安全说明" description="导入导出均为高风险管理员操作。若接口返回 404/500/权限错误，页面会如实显示，不会制造成功提示。" />
      </div>
    </PagePlaceholder>
  )
}
