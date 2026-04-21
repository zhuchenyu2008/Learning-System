import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FileText, FolderTree, Search, Trash2 } from 'lucide-react'
import type { NoteType, NoteTreeNode } from '@/types/notes'
import { NoteDetailRenderer } from '@/components/note-detail-renderer'
import { notesApi } from '@/lib/notes-api'

const MIN_WATCH_SECONDS_TO_REPORT = 3
const MAIN_LIBRARY_NOTE_TYPES: NoteType[] = ['source_note', 'review_note']

function TreeNodeItem({
  node,
  selectedNoteId,
  onSelect,
}: {
  node: NoteTreeNode
  selectedNoteId: number | null
  onSelect: (noteId: number) => void
}) {
  const [expanded, setExpanded] = useState(true)
  const isSelected = node.note_id != null && node.note_id === selectedNoteId

  if (node.is_dir) {
    return (
      <div className="space-y-2">
        <button type="button" className="flex w-full items-center gap-2 rounded-lg px-2 py-1 text-left text-sm text-cloth-ink hover:bg-white/50" onClick={() => setExpanded((value) => !value)}>
          <FolderTree className="h-4 w-4 text-cloth-accent" />
          <span className="font-medium">{node.name}</span>
        </button>
        {expanded ? (
          <div className="ml-4 space-y-2 border-l border-cloth-line/60 pl-3">
            {node.children.map((child) => (
              <TreeNodeItem key={child.path} node={child} selectedNoteId={selectedNoteId} onSelect={onSelect} />
            ))}
          </div>
        ) : null}
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={() => node.note_id && onSelect(node.note_id)}
      className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm ${isSelected ? 'bg-white/80 text-cloth-ink shadow-sm' : 'text-cloth-muted hover:bg-white/45 hover:text-cloth-ink'}`}
    >
      <FileText className="h-4 w-4" />
      <span className="truncate">{node.name}</span>
    </button>
  )
}

export function NotesLibraryPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [noteType, setNoteType] = useState<NoteType | 'all'>('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null)
  const activeNoteRef = useRef<number | null>(null)
  const activeNoteStartedAtRef = useRef<number | null>(null)

  const flushWatchSeconds = (reason: 'switch' | 'hidden' | 'pagehide' | 'unmount') => {
    const noteId = activeNoteRef.current
    const startedAt = activeNoteStartedAtRef.current
    if (!noteId || !startedAt) return

    const elapsedSeconds = Math.floor((Date.now() - startedAt) / 1000)
    if (elapsedSeconds >= MIN_WATCH_SECONDS_TO_REPORT) {
      void notesApi.reportWatchSeconds(noteId, elapsedSeconds)
    }

    if (reason !== 'switch') {
      activeNoteStartedAtRef.current = Date.now()
    }
  }

  const notesQuery = useQuery({ queryKey: ['notes', 'library'], queryFn: () => notesApi.listNotes() })
  const treeQuery = useQuery({ queryKey: ['notes-tree', 'library'], queryFn: () => notesApi.getNotesTree() })
  const noteDetailQuery = useQuery({
    queryKey: ['note-detail', selectedNoteId],
    queryFn: () => notesApi.getNoteDetail(selectedNoteId as number),
    enabled: selectedNoteId != null,
  })

  const deleteMutation = useMutation({
    mutationFn: (noteId: number) => notesApi.deleteNote(noteId),
    onSuccess: async (_, deletedNoteId) => {
      if (selectedNoteId === deletedNoteId) {
        setSelectedNoteId(null)
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['notes', 'library'] }),
        queryClient.invalidateQueries({ queryKey: ['notes-tree', 'library'] }),
        queryClient.invalidateQueries({ queryKey: ['note-detail', deletedNoteId] }),
      ])
    },
  })

  const filteredNotes = useMemo(() => {
    const notes = notesQuery.data ?? []
    return notes.filter((note) => {
      const searchMatched = !search || note.title.toLowerCase().includes(search.toLowerCase()) || note.relative_path.toLowerCase().includes(search.toLowerCase())
      const typeMatched = noteType === 'all' ? MAIN_LIBRARY_NOTE_TYPES.includes(note.note_type) : note.note_type === noteType
      const sourceMatched = sourceFilter === 'all' || (sourceFilter === 'linked' ? note.source_asset_id != null : note.source_asset_id == null)
      return searchMatched && typeMatched && sourceMatched
    })
  }, [noteType, notesQuery.data, search, sourceFilter])

  useEffect(() => {
    if (!selectedNoteId && filteredNotes[0]) {
      setSelectedNoteId(filteredNotes[0].id)
      return
    }
    if (selectedNoteId && filteredNotes.every((note) => note.id !== selectedNoteId)) {
      setSelectedNoteId(filteredNotes[0]?.id ?? null)
    }
  }, [filteredNotes, selectedNoteId])

  useEffect(() => {
    if (activeNoteRef.current && activeNoteRef.current !== selectedNoteId) {
      flushWatchSeconds('switch')
    }

    activeNoteRef.current = selectedNoteId
    activeNoteStartedAtRef.current = selectedNoteId ? Date.now() : null
  }, [selectedNoteId])

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        flushWatchSeconds('hidden')
      }
    }

    const handlePageHide = () => {
      flushWatchSeconds('pagehide')
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('pagehide', handlePageHide)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('pagehide', handlePageHide)
      flushWatchSeconds('unmount')
    }
  }, [])

  const handleDeleteNote = (noteId: number, title: string) => {
    if (!window.confirm(`确认删除笔记《${title}》？此操作会同时删除对应文件。`)) return
    deleteMutation.mutate(noteId)
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,280px)_minmax(0,360px)_minmax(0,1fr)]">
      <section className="fabric-panel min-h-[720px] min-w-0 overflow-hidden">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Directory Tree</p>
          <h1 className="mt-1 font-serif text-2xl text-cloth-ink">笔记目录</h1>
          <p className="mt-2 text-sm text-cloth-muted">主笔记库默认仅展示 source_note / review_note；summary 与 mindmap 请前往各自产物页面查看。</p>
        </div>
        <div className="mt-4 max-h-[620px] space-y-3 overflow-auto pr-1 scrollbar-thin">
          {treeQuery.data?.length ? (
            treeQuery.data.map((node) => (
              <TreeNodeItem key={node.path} node={node} selectedNoteId={selectedNoteId} onSelect={setSelectedNoteId} />
            ))
          ) : (
            <div className="fabric-card text-sm text-cloth-muted">暂无目录树数据。</div>
          )}
        </div>
      </section>

      <section className="fabric-panel min-h-[720px] min-w-0 overflow-hidden">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Note Library</p>
          <h2 className="mt-1 font-serif text-2xl text-cloth-ink">笔记库</h2>
        </div>
        <div className="mt-4 space-y-3">
          {deleteMutation.isError ? <div className="rounded-xl border border-cloth-danger/40 bg-cloth-danger/10 p-3 text-sm text-cloth-ink">{String((deleteMutation.error as Error | null)?.message ?? '删除失败')}</div> : null}
          <label className="relative block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-cloth-muted" />
            <input value={search} onChange={(event) => setSearch(event.target.value)} className="fabric-input pl-10" placeholder="搜索标题或路径" />
          </label>
          <div className="grid gap-3 md:grid-cols-2">
            <select
              value={noteType}
              onChange={(event) => {
                const value = event.target.value
                if (value === 'all' || value === 'source_note' || value === 'review_note') {
                  setNoteType(value)
                }
              }}
              className="fabric-input"
            >
              <option value="all">主笔记（默认）</option>
              <option value="source_note">source_note</option>
              <option value="review_note">review_note</option>
            </select>
            <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)} className="fabric-input">
              <option value="all">全部来源</option>
              <option value="linked">仅有关联来源</option>
              <option value="orphan">仅无来源关联</option>
            </select>
          </div>
        </div>
        <div className="mt-4 max-h-[560px] space-y-3 overflow-auto pr-1 scrollbar-thin">
          {filteredNotes.length ? (
            filteredNotes.map((note) => {
              const selected = note.id === selectedNoteId
              const deleting = deleteMutation.isPending && deleteMutation.variables === note.id
              return (
                <div key={note.id} className={`rounded-xl border p-4 ${selected ? 'border-cloth-accent/55 bg-white/85 shadow-panel' : 'border-cloth-line/70 bg-white/45 hover:bg-white/65'}`}>
                  <div className="flex items-start justify-between gap-3">
                    <button type="button" onClick={() => setSelectedNoteId(note.id)} className="min-w-0 flex-1 text-left">
                      <p className="truncate text-sm font-semibold text-cloth-ink">{note.title}</p>
                      <p className="mt-1 truncate text-xs text-cloth-muted">{note.relative_path}</p>
                    </button>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-cloth-panel px-2 py-1 text-xs text-cloth-muted">{note.note_type}</span>
                      <button
                        type="button"
                        className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-cloth-line/70 bg-white/80 text-cloth-muted transition hover:text-cloth-danger disabled:cursor-not-allowed disabled:opacity-60"
                        onClick={() => handleDeleteNote(note.id, note.title)}
                        disabled={deleting}
                        aria-label={`删除 ${note.title}`}
                        title="删除笔记"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )
            })
          ) : (
            <div className="fabric-card text-sm text-cloth-muted">没有匹配当前筛选条件的笔记。</div>
          )}
        </div>
      </section>

      <section className="fabric-panel min-h-[720px] min-w-0 overflow-hidden">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-cloth-muted">Detail Renderer</p>
          <h2 className="mt-1 font-serif text-2xl text-cloth-ink">笔记详情</h2>
        </div>
        <div className="mt-4 min-w-0">
          {noteDetailQuery.data ? (
            <NoteDetailRenderer note={noteDetailQuery.data} />
          ) : (
            <div className="fabric-card text-sm text-cloth-muted">请选择一篇笔记查看详情。</div>
          )}
        </div>
      </section>
    </div>
  )
}
