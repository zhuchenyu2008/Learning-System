import type { ArtifactGenerateResult, JobRecord } from '@/types/notes'

export type ArtifactJobVisualStatus = 'queued' | 'running' | 'completed' | 'failed'

export function normalizeArtifactJobStatus(status: string | undefined): ArtifactJobVisualStatus {
  if (status === 'running') return 'running'
  if (status === 'completed') return 'completed'
  if (status === 'failed') return 'failed'
  return 'queued'
}

function readResultValue<T>(job: JobRecord | null | undefined, key: string): T | null {
  const result = job?.result_json
  if (!result || typeof result !== 'object') return null
  const value = result[key]
  return (value as T | null | undefined) ?? null
}

export function getArtifactOutputNoteId(job: JobRecord | null | undefined, fallback: ArtifactGenerateResult | null): number | null {
  const fromJob = readResultValue<number>(job, 'output_note_id')
  if (typeof fromJob === 'number' && fromJob > 0) return fromJob
  return typeof fallback?.output_note_id === 'number' && fallback.output_note_id > 0 ? fallback.output_note_id : null
}

export function getArtifactStatusMessage(
  label: string,
  job: JobRecord | null | undefined,
  fallback: ArtifactGenerateResult | null,
) {
  if (!fallback) return null

  const normalizedStatus = normalizeArtifactJobStatus(job?.status ?? fallback.status)
  const jobId = job?.id ?? fallback.job_id
  const artifactId = readResultValue<number>(job, 'artifact_id') ?? fallback.artifact_id
  const outputNoteId = getArtifactOutputNoteId(job, fallback)
  const relativePath = readResultValue<string>(job, 'relative_path') ?? fallback.relative_path

  if (normalizedStatus === 'failed') {
    return {
      tone: 'error' as const,
      text: `任务 #${jobId} ${label}生成失败${job?.error_message ? `：${job.error_message}` : '。'}`,
    }
  }

  if (normalizedStatus === 'completed') {
    const resultParts = [
      artifactId ? `产物 #${artifactId}` : null,
      outputNoteId ? `输出笔记 #${outputNoteId}` : null,
      relativePath ? `路径 ${relativePath}` : null,
    ].filter(Boolean)

    return {
      tone: 'success' as const,
      text: resultParts.length
        ? `任务 #${jobId} 已完成，${resultParts.join('，')}。`
        : `任务 #${jobId} 已完成，${label}结果已就绪。`,
    }
  }

  if (normalizedStatus === 'running') {
    return {
      tone: 'info' as const,
      text: `任务 #${jobId} 正在生成${label}，请稍候…`,
    }
  }

  return {
    tone: 'info' as const,
    text: `任务 #${jobId} 已创建，正在排队生成${label}…`,
  }
}
