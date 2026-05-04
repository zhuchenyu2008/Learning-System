# Learning-System Frontend Design for Stitch

## 1. Product Context

Learning-System is a web app for turning classroom materials into structured study notes, review cards, RAG Q&A, summaries, mind maps, and Obsidian-friendly Markdown exports.

Design the actual application workspace, not a marketing landing page.

Primary users:

- Admin: uploads materials, generates notes, manages cards, edits content, configures AI and Obsidian, reviews tasks and user activity.
- User: reads notes, asks questions, reviews cards, views summaries and mind maps. Disabled admin actions remain visible with clear disabled states.

## 2. Visual Thesis

A calm study workspace with tactile woven material: light linen background, canvas-like work surfaces, stitched dividers, restrained neutral colors, and small ink-and-thread accents for action and status.

The interface should feel focused, crafted, readable, and slightly warm. It should not feel like a marketing SaaS dashboard, a glossy AI toy, or a card-heavy analytics template.

## 3. Interaction Thesis

- Navigation feels like opening sections in a study binder: the left tree expands and collapses smoothly.
- Long AI workflows feel observable: upload, parsing, generation, indexing, and export states appear in compact progress bands.
- Reading and review interactions feel quiet and deliberate: answer reveal, source expansion, and markdown details use short, soft transitions.

Motion should be subtle, 180-260ms, and never distract from reading.

## 4. App Shell

Use a fixed desktop layout:

```text
Left sidebar navigation | Single main workspace
```

Do not create a left-middle-right three-column workbench inside the main area. The main workspace can use top status bands, inline sections, tabs, drawers, or bottom detail areas, but not a permanent three-column business layout.

### Left Sidebar

Width: about 248px on desktop.

Visual:

- Linen or muted canvas texture.
- Slight stitched vertical separator.
- Product name at top: `Learning-System`.
- Tree navigation with three expandable first-level modules.
- Current item uses a stitched left accent or cloth-tab highlight.

Navigation:

```text
学习
  总览
  笔记生成
  笔记库
  RAG 问答

复习
  总览
  复习
  知识点总结
  思维导图生成

设置
  AI 配置
  Obsidian 配置
  用户与权限
  数据导入导出
  任务与系统日志
```

Use simple line icons if available. Do not use decorative icons that slow scanning.

### Main Workspace

Main area:

- Single working surface.
- Max content width may be constrained for reading pages, but operational pages can use the full available width.
- Use section dividers, tabs, tables, editors, progress bands, and drawers instead of nested cards.
- Repeated items may use small cards with radius no more than 8px.

### Mobile

Use:

- Top app bar with current module.
- Drawer navigation for the full tree.
- Optional bottom navigation for the three first-level modules.
- Single-column main content.
- Context panels open as bottom sheets or drawers.

## 5. Visual System

### Palette

Use warm neutrals with one primary accent and a few semantic colors.

Suggested tokens:

- App background: warm linen `#F4F0E7`
- Main surface: soft canvas `#FBF8F0`
- Raised surface: paper `#FFFDF7`
- Primary text: ink `#24211C`
- Secondary text: muted graphite `#696256`
- Border/stitch: flax thread `#D8CCB8`
- Primary accent: walnut-brown thread `#7A4F2B`
- Secondary accent: moss `#6E7F5E`
- Warning: ochre `#B7791F`
- Danger: muted red `#B75D55`
- Success: sage `#5F8A70`

Avoid a one-note beige interface. Balance the warm woven base with ink, walnut-brown, sage, ochre, and muted red.

### Typography

Use readable product typography:

- Sans-serif UI font for navigation, controls, labels, and tables.
- Optional serif only for long-form note titles or markdown reading headers.
- No viewport-based font scaling.
- Letter spacing should be 0.

Suggested hierarchy:

- Page title: 28-34px desktop, 22-26px mobile.
- Section heading: 18-22px.
- Body: 15-16px.
- Labels and metadata: 12-13px.

### Shape And Texture

- Radius: 6-8px for cards, inputs, buttons, and tables.
- Avoid large pill shapes unless used for compact filters or tags.
- Use stitched borders sparingly.
- Texture must be subtle and should not reduce text contrast.
- Keep shadows soft and low. The design should still work if shadows are removed.

## 6. Global Components

### Buttons

Primary button:

- Cloth-label style.
- Walnut-brown background or walnut-brown border.
- Clear icon + text when the action is important.

Secondary button:

- Transparent or paper surface.
- Thin flax border.

Danger button:

- Muted red.
- No aggressive neon colors.

Disabled buttons:

- Low saturation gray-brown.
- Tooltip text: `需要管理员权限`.
- Disabled state must be visibly disabled, not hidden.

### Status Bands

Use compact horizontal bands for asynchronous work:

- Queued
- Running
- Waiting for input
- Succeeded
- Failed
- Retrying
- Cancelled

Each band includes:

- Status icon.
- Short label.
- Progress indicator when available.
- Last update time.
- Action buttons if allowed: retry, cancel, view logs.

### Tables And Lists

Use dense but readable tables for operational screens:

- Clear column labels.
- Sticky header when long.
- Row hover with soft canvas tint.
- Inline status badges.
- Bulk actions only where necessary.

### Drawers

Use drawers for:

- Source citations.
- Note metadata.
- Task logs.
- User activity details.
- Export details.

Drawers should not permanently split the page into three columns.

### Markdown Viewer

Support visual states for:

- GitHub Flavored Markdown.
- KaTeX formulas.
- Mermaid diagrams.
- Markmap mind maps.
- Tables.
- Code blocks.
- Blockquotes.
- Attachments and source citations.

Code blocks use quiet ink-on-paper styling. Tables must horizontally scroll on mobile.

## 7. Key Screens

### 7.1 学习 / 总览

Route: `/notes`

Purpose: show the current learning pipeline state and recent study content.

Layout:

- Page title: `学习总览`
- Top status band with upload, parse, note generation, indexing, and export health.
- Admin quick actions: upload material, continue unfinished generation.
- Recent notes list.
- Recent RAG questions list.
- Compact task activity strip.

For normal users:

- Upload and generation actions remain visible but disabled.
- Primary focus becomes recent notes and recent Q&A.

Visual direction:

- Quiet operational surface.
- No hero section.
- Use grouped rows and dividers instead of dashboard card mosaics.

### 7.2 学习 / 笔记生成

Route: `/notes/generate`

Purpose: upload classroom materials, inspect parsed segments, and generate Markdown notes.

Layout:

- Page title: `笔记生成`
- Upload zone at top with supported file types.
- Source file list.
- Parsed segment selector.
- Generation settings row: subject, class time, optional admin note.
- Main action: `生成课堂笔记`
- Generation progress band.
- Generated note preview after completion.

Admin:

- Can upload, parse, select sources, and generate.

User:

- Upload and generate controls disabled with tooltip.
- Can inspect generated examples only if content exists.

Interaction:

- Drag upload hover subtly raises the cloth edge.
- Segment selection uses checkboxes.
- Generation progress steps animate in sequence.

### 7.3 学习 / 笔记库

Route: `/notes/library`

Purpose: browse, filter, read, and manage notes.

Layout:

- Page title: `笔记库`
- Filter row: search, subject, type, index state, export state.
- Compact subject/type file tree.
- Selected note opens in the main reading area.
- Metadata, edit, delete, rebuild index, and re-export controls sit above the note body.
- Source citations and related content open in drawer or below the reading area.
- Notes do not have draft/published states.

Admin actions:

- Edit.
- Delete.
- Rebuild index.
- Re-export.

User:

- Read-only.
- Admin actions disabled.

Reading view:

- Strong markdown readability.
- Source citations appear as inline markers and drawer details.

### 7.4 学习 / RAG 问答

Route: `/notes/qa`

Purpose: ask questions against the note knowledge base with citations.

Layout:

- Page title: `RAG 问答`
- ChatGPT-like conversation workspace.
- Central message transcript with the AI answer and citations attached below the assistant message.
- Sticky bottom composer with question input and optional filters: subject, content type, date range.
- Retrieved chunks and citations open in drawer.
- Question history is secondary and should not dominate the workspace.

Interaction:

- Streaming answer uses calm line-by-line reveal.
- Citation hover highlights source.
- Empty state says there is not enough indexed content if no sources exist.

Rules:

- Answers must show citations.
- If no reliable source is found, show a clear insufficient-evidence state.

### 7.5 复习 / 总览

Route: `/review`

Purpose: show due cards, backlog, completion, accuracy, weak subjects, and FSRS distribution.

Layout:

- Page title: `复习总览`
- Due summary strip: due now, backlog, completed today, accuracy.
- FSRS distribution chart.
- Weak subject list.
- Recent review logs.
- Admin can switch scope: self, all users, selected user.

Avoid decorative chart cards. Use clean chart regions with clear labels.

### 7.6 复习 / 复习

Route: `/review/session`

Purpose: answer due cards and update FSRS scheduling.

Layout:

- Page title: `复习`
- One focused card area.
- Question.
- Answer input.
- Submit answer button.
- AI feedback section after submission.
- AI suggests Again, Hard, Good, or Easy from the submitted answer.
- User controls are limited to confirming the AI score or answering again.
- Next due time preview.
- Bad-card feedback action.

Visual:

- This page can use a single centered review card because the card is the interaction.
- Keep the rest of the UI quiet.

Interaction:

- Answer reveal slides softly.
- Rating buttons use stable sizes and semantic color hints.
- Next card transition is quick and deliberate.

### 7.7 复习 / 知识点总结

Route: `/review/summaries`

Purpose: view and generate knowledge summaries.

Layout:

- Page title: `知识点总结`
- Two modes: 查看 and 生成.
- 查看 uses a compact file tree and Markdown summary viewer.
- 生成 lets admins check source notes, set title/subject/options, and submit an async generation job.
- Generation progress band.

User:

- Can view summaries.
- Generation controls disabled.

### 7.8 复习 / 思维导图生成

Route: `/review/mind-maps`

Purpose: view and generate interactive mind maps.

Layout:

- Page title: `思维导图`
- Two modes: 查看 and 生成.
- 查看 uses a compact file tree and the main Markmap canvas.
- 生成 mirrors knowledge summaries: admins check source notes, set depth/options, and submit an async generation job.
- Mermaid-compatible source remains available for export.

Visual:

- Markmap canvas should be large and uncluttered.
- Do not place the map inside a decorative heavy card.

### 7.9 设置 / AI 配置

Route: `/settings/ai`

Purpose: configure OpenAI-compatible model providers.

Layout:

- Page title: `AI 配置`
- Model purpose sections:
  - 笔记生成
  - Embedding
  - 语音转文字
  - OCR / 视觉理解
  - Reranker
  - AI 评分
- Fields: provider label, base URL, model name, API key.
- Connection test button.
- Last test status.
- Prompt settings area.

Security UI:

- API key field masks value.
- Existing key displays only tail, such as `sk-...abcd`.
- Never show full key in preview, logs, or status.

### 7.10 设置 / Obsidian 配置

Route: `/settings/obsidian`

Purpose: configure local Markdown export.

Layout:

- Page title: `Obsidian 配置`
- Vault path.
- Export root.
- Export strategy toggles.
- Test write button.
- Recent export status.
- Path mapping note for Docker deployments.

Make path fields readable and easy to copy visually, but keep them as inputs or code-style text areas.

### 7.11 设置 / 用户与权限

Route: `/settings/users`

Purpose: manage registration, users, roles, sessions, viewing duration, and review activity.

Layout:

- Page title: `用户与权限`
- Registration switch.
- User table.
- Role controls.
- Session activity.
- Viewing duration summary.
- Review activity drawer.

Only admin can modify roles or registration. Normal users should see settings entries disabled or blocked by permission state.

### 7.12 设置 / 数据导入导出

Route: `/settings/data`

Purpose: run database backup export and import.

Layout:

- Page title: `数据导入导出`
- Export backup section.
- Import backup section.
- Manifest validation result.
- Conflict strategy preview.
- Job history table.

Security:

- Clearly state that backup packages must not include plaintext API keys.
- Import must show validation before final action.

### 7.13 设置 / 任务与系统日志

Route: `/settings/tasks`

Purpose: inspect asynchronous jobs, failures, retries, cancellations, system logs, and audit logs.

Layout:

- Page title: `任务与系统日志`
- Job status tabs.
- Job table.
- Selected job log drawer.
- Retry and cancel actions for admin.
- Audit log table.

Failure states must be human-readable and must not leak secrets.

## 8. Empty, Loading, Error, And Permission States

### Empty States

Use concise product UI copy:

- No notes: `暂无笔记`
- No indexed content: `当前知识库还没有可检索内容`
- No due cards: `当前没有到期卡片`
- No tasks: `暂无任务记录`

Do not use marketing copy or long explanations.

### Loading States

Use skeleton rows for tables and lists. Use progress bands for long tasks.

### Error States

Errors should include:

- What failed.
- What the user can do next.
- Whether admin permission is required.

Never expose API keys or raw stack traces.

### Permission States

Disabled admin-only controls remain visible:

- Disabled style.
- Tooltip: `需要管理员权限`.
- Optional lock icon.

Backend permission is mandatory, but the UI should make the role boundary understandable.

## 9. Responsive Requirements

Desktop:

- Sidebar fixed.
- Main workspace scrolls.
- Tables can use full width.
- Drawers open from the right.

Tablet:

- Sidebar may collapse.
- Filters wrap into two rows.
- Drawers can cover more width.

Mobile:

- Drawer navigation.
- Single-column content.
- Tables become stacked rows or horizontal scroll.
- Long markdown, formulas, code blocks, and tables must not overflow the viewport.
- Primary actions remain reachable at the bottom or near the current task.

## 10. Accessibility Requirements

- Strong text contrast over all textures.
- Visible focus states.
- Keyboard navigable sidebar, tabs, drawers, tables, and review rating controls.
- Form labels must be explicit.
- Icons need accessible labels or adjacent text.
- Status colors must be paired with text or icons.

## 11. Stitch Generation Prompt

Use this as the concise generation brief:

```text
Create the frontend UI for Learning-System, a classroom learning workspace that turns uploaded materials into Markdown notes, review cards, RAG Q&A, summaries, mind maps, and Obsidian exports.

Build an actual app workspace, not a landing page.

Use a fixed desktop shell with a 248px left tree sidebar and one single main workspace. The sidebar has three expandable modules: 学习, 复习, 设置. 学习 contains 总览, 笔记生成, 笔记库, RAG 问答. 复习 contains 总览, 复习, 知识点总结, 思维导图生成. 设置 contains AI 配置, Obsidian 配置, 用户与权限, 数据导入导出, 任务与系统日志.

Visual style: warm woven material, light linen background, soft canvas surfaces, stitched dividers, high-contrast ink typography, walnut-brown thread as the primary accent, sage, ochre, and muted red for semantic states. Keep the UI calm, dense, readable, and product-focused. Avoid marketing hero sections, dashboard card mosaics, nested cards, bright gradients, and three-column workbench layouts.

Design the key screens: 学习总览, 笔记生成, 笔记库, RAG 问答, 复习总览, 复习, 知识点总结, 思维导图, AI 配置, Obsidian 配置, 用户与权限, 数据导入导出, 任务与系统日志.

Admin actions are visible and enabled for admins. Normal users see the same interface, but upload, generate, edit, delete, configure, import, export, retry, and cancel actions are disabled with tooltip text “需要管理员权限”.

Use compact progress bands for async jobs: queued, running, waiting input, succeeded, failed, retrying, cancelled. Use drawers for citations, metadata, task logs, user activity, and export details. Markdown viewer supports GFM, KaTeX, Mermaid, Markmap, tables, code blocks, blockquotes, citations, and attachments.

Use subtle motion: sidebar expand/collapse, progress step transitions, answer reveal, citation drawer, and row hover. Motion should be restrained and 180-260ms.

Responsive behavior: desktop fixed sidebar, tablet collapsible sidebar, mobile drawer navigation and single-column content. Tables and markdown must not overflow on mobile.
```

## 12. Final Quality Checklist

- First screen is an app workspace, not a hero page.
- Product name and current module are immediately clear.
- Sidebar tree is understandable and expandable.
- Main workspace never becomes left-middle-right business columns.
- Texture is visible but does not harm readability.
- Cards are only used for repeated items or the review card interaction.
- Admin-only controls remain visible in disabled state for normal users.
- Async task progress is easy to understand.
- Markdown reading is comfortable.
- Mobile layout is single-column and overflow-safe.
