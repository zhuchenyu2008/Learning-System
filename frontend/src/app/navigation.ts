import { BookOpenText, BrainCircuit, FolderKanban, Lock, NotebookPen, Settings2, ShieldCheck, Sparkles, UserCog, Workflow } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { UserRole } from '@/types/auth'

export interface NavLeaf {
  label: string
  path: string
  adminOnly?: boolean
}

export interface NavSection {
  label: string
  icon: LucideIcon
  path: string
  children: NavLeaf[]
}

export const navSections: NavSection[] = [
  {
    label: '笔记',
    icon: NotebookPen,
    path: '/notes',
    children: [
      { label: '总览', path: '/notes/overview' },
      { label: '笔记生成', path: '/notes/generate', adminOnly: true },
      { label: '笔记库', path: '/notes/library' },
    ],
  },
  {
    label: '复习',
    icon: BrainCircuit,
    path: '/review',
    children: [
      { label: '总览', path: '/review/overview' },
      { label: '复习', path: '/review/session' },
      { label: '知识点总结', path: '/review/summaries', adminOnly: true },
      { label: '思维导图', path: '/review/mindmaps', adminOnly: true },
    ],
  },
  {
    label: '设置',
    icon: Settings2,
    path: '/settings',
    children: [
      { label: 'AI 配置', path: '/settings/ai', adminOnly: true },
      { label: '工作目录与同步', path: '/settings/workspace', adminOnly: true },
      { label: '用户与审计', path: '/settings/users', adminOnly: true },
      { label: '导入导出', path: '/settings/import-export', adminOnly: true },
      { label: '任务策略', path: '/settings/jobs', adminOnly: true },
    ],
  },
]

export const shellQuickLinks = [
  { label: '工作区', icon: FolderKanban },
  { label: 'AI 任务', icon: Workflow },
  { label: '阅读体验', icon: BookOpenText },
  { label: '织物主题', icon: Sparkles },
]

export const roleMeta: Record<UserRole, { label: string; icon: LucideIcon; description: string }> = {
  admin: {
    label: '管理员',
    icon: ShieldCheck,
    description: '可配置系统、导入资料并触发生成任务',
  },
  viewer: {
    label: '普通用户',
    icon: Lock,
    description: '可阅读内容并提交复习结果，管理操作保持禁用',
  },
}

export const userMenuItems = [
  { label: '账户状态', icon: UserCog },
]
