/** Active ctxvm stub-mode selection, protection, pinning, and stub-text helpers. */
export interface ActiveEngineConfig {
  budgetTokens: number
  protectFirstN: number
  protectLastN: number
  stubDropped: 'off' | 'recoverable'
  selectionMode: 'fresh' | 'stable'
  stableEvery: number
}

export interface EngineBlock {
  type: string
  text?: string
  name?: string
  arguments?: string
  id?: string
}

export interface EngineMessage {
  role: string
  content: readonly EngineBlock[]
  toolCallId?: string
  id?: unknown
}

export interface PageCandidate {
  seq: number
  ref: string
  contentHash: string
  tokens: number
  name: string
  args: unknown
  callId: string
  messageIndex: number
  text: string
}

export interface ActivePageState {
  demandCount: number
  lastSeq: number
  pinned: boolean
  tokens: number
}

export interface HeldSelection {
  keys: string[]
  dropped: string[]
  callsSincePlan: number
}

export interface ActiveSessionState {
  pages: Map<string, ActivePageState>
  identityActive: Map<string, string>
  pinOrder: string[]
  stubbedKeys: Set<string>
  held?: HeldSelection
  diagnostics: string[]
}

export interface ActivePlan {
  selected: PageCandidate[]
  reason: 'fits' | 'floor_bust' | 'evicted'
  floorTokens: number
  residentTokens: number
  droppedTokens: number
  measuredTokens?: number
  trigger?: 'new-page' | 'overflow' | 'every-B' | 'held'
}

const READ_ONLY_TOOLS = new Set(['read_file', 'search_files'])
const ARG_LIMIT = 200
const MESSAGE_OVERHEAD = 4

export function createActiveSessionState(): ActiveSessionState {
  return { pages: new Map(), identityActive: new Map(), pinOrder: [], stubbedKeys: new Set(), diagnostics: [] }
}

export function pageKey(candidate: Pick<PageCandidate, 'ref' | 'contentHash'>): string {
  return `${candidate.ref}\u0000${candidate.contentHash}`
}

export function textOfContent(content: unknown): string {
  if (typeof content === 'string') return content
  if (Array.isArray(content)) {
    return content.filter(block => block !== null && typeof block === 'object'
      && (block as { type?: unknown }).type === 'text')
      .map(block => typeof (block as { text?: unknown }).text === 'string'
        ? (block as { text: string }).text : '')
      .join('')
  }
  return content === undefined || content === null ? '' : JSON.stringify(content)
}

function messageText(message: EngineMessage): string {
  const parts: string[] = []
  for (const block of message.content) {
    if (block.type === 'text' || block.type === 'reasoning') parts.push(block.text ?? '')
    else if (block.type === 'tool-call') parts.push(block.name ?? '', block.arguments ?? '')
    else parts.push(`<${block.type}${block.name === undefined ? '' : `:${block.name}`}>`)
  }
  if (message.toolCallId !== undefined) parts.push(message.toolCallId)
  return parts.filter(Boolean).join('\n')
}

/** Hermes L6: ceil(chars/4) plus four structural tokens per message. */
export function estimateEngineMessage(message: EngineMessage): number {
  return MESSAGE_OVERHEAD + Math.ceil([...messageText(message)].length / 4)
}

function diagnostic(state: ActiveSessionState, message: string): void {
  state.diagnostics.push(message)
  if (state.diagnostics.length > 100) state.diagnostics.shift()
}

function pin(state: ActiveSessionState, key: string): void {
  const page = state.pages.get(key)
  if (page === undefined || page.pinned) return
  page.pinned = true
  state.pinOrder.push(key)
}

function release(state: ActiveSessionState, key: string): void {
  const page = state.pages.get(key)
  if (page !== undefined) page.pinned = false
  state.pinOrder = state.pinOrder.filter(candidate => candidate !== key)
}

/** L3/L4: first render is demand one; a new result for the same PageId is demand two. */
function observeCandidates(state: ActiveSessionState, candidates: readonly PageCandidate[]): void {
  for (const candidate of [...candidates].sort((left, right) => left.messageIndex - right.messageIndex)) {
    const key = pageKey(candidate)
    state.stubbedKeys.delete(key)
    const existing = state.pages.get(key)
    if (existing === undefined) {
      state.pages.set(key, { demandCount: 1, lastSeq: candidate.seq, pinned: false, tokens: candidate.tokens })
    } else if (existing.lastSeq !== candidate.seq) {
      existing.lastSeq = candidate.seq
      existing.demandCount++
      existing.tokens = Math.max(existing.tokens, candidate.tokens)
      if (existing.demandCount >= 2) pin(state, key)
    }
    const active = state.identityActive.get(candidate.ref)
    if (active !== undefined && active !== key) release(state, active)
    state.identityActive.set(candidate.ref, key)
  }
}

export function hardKeepIndices(
  messages: readonly EngineMessage[],
  candidates: readonly PageCandidate[],
  config: ActiveEngineConfig,
): Set<number> {
  const keep = new Set<number>()
  const nonSystem: number[] = []
  for (let index = 0; index < messages.length; index++) {
    if (messages[index]?.role === 'system') keep.add(index)
    else nonSystem.push(index)
  }
  if (config.protectFirstN > 0) for (const index of nonSystem.slice(0, config.protectFirstN)) keep.add(index)
  if (config.protectLastN > 0) for (const index of nonSystem.slice(-config.protectLastN)) keep.add(index)

  const answered = new Set(messages.filter(message => message.role === 'tool')
    .map(message => message.toolCallId).filter((id): id is string => typeof id === 'string'))
  let lastUser: number | undefined
  for (let index = 0; index < messages.length; index++) {
    const message = messages[index]
    if (message === undefined) continue
    if (message.role === 'user') lastUser = index
    if (message.role === 'assistant' && message.content.some(block => block.type === 'tool-call'
      && typeof block.id === 'string' && !answered.has(block.id))) keep.add(index)
  }
  if (lastUser !== undefined) keep.add(lastUser)

  // A candidate itself may be protected by the head/tail law.
  for (const candidate of candidates) if (keep.has(candidate.messageIndex)) keep.add(candidate.messageIndex)
  return keep
}

function stableTrigger(
  state: ActiveSessionState,
  candidates: readonly PageCandidate[],
  residentTokens: number,
  config: ActiveEngineConfig,
): 'new-page' | 'overflow' | 'every-B' | undefined {
  const held = state.held
  if (held === undefined) return undefined
  held.callsSincePlan++
  const present = new Map(candidates.map(candidate => [pageKey(candidate), candidate]))
  const heldKeys = new Set(held.keys)
  if (candidates.some(candidate => !heldKeys.has(pageKey(candidate)))) return 'new-page'
  if (held.dropped.some(key => !present.has(key) && !state.stubbedKeys.has(key))) return 'new-page'
  const outgoing = residentTokens - held.dropped.reduce((sum, key) => sum + (present.get(key)?.tokens ?? 0), 0)
  if (outgoing > config.budgetTokens) return 'overflow'
  if (held.callsSincePlan >= config.stableEvery) return 'every-B'
  return undefined
}

/** Select the oldest unpinned pages that must be stubbed to fit the budget. */
export function planActiveStub(
  messages: readonly EngineMessage[],
  candidates: readonly PageCandidate[],
  config: ActiveEngineConfig,
  state: ActiveSessionState,
  measuredTokens?: number,
): ActivePlan {
  observeCandidates(state, candidates)
  const hardKeep = hardKeepIndices(messages, candidates, config)
  const candidateIndices = new Set(candidates.map(candidate => candidate.messageIndex))
  const residentTokens = messages.reduce((sum, message) => sum + estimateEngineMessage(message), 0)
  const floorTokens = [...hardKeep].reduce((sum, index) => sum + estimateEngineMessage(messages[index] as EngineMessage), 0)
  if (floorTokens >= config.budgetTokens) {
    return { selected: [], reason: 'floor_bust', floorTokens, residentTokens, droppedTokens: 0, measuredTokens }
  }

  const seenKeys = new Set<string>()
  for (const candidate of candidates) {
    const key = pageKey(candidate)
    if (seenKeys.has(key)) {
      diagnostic(state, `duplicate current PageId ${key}; active selection skipped`)
      return { selected: [], reason: 'fits', floorTokens, residentTokens, droppedTokens: 0, measuredTokens }
    }
    seenKeys.add(key)
  }
  const scaffoldTokens = messages.reduce((sum, message, index) => sum
    + (!hardKeep.has(index) && !candidateIndices.has(index) ? estimateEngineMessage(message) : 0), 0)
  const byKey = new Map(candidates.map(candidate => [pageKey(candidate), candidate]))
  const tokensFor = (key: string): number => state.pages.get(key)?.tokens ?? byKey.get(key)?.tokens ?? 0
  const pinnedKeys = state.pinOrder.filter(key => byKey.has(key))
  const pinnedTokens = pinnedKeys.reduce((sum, key) => sum + tokensFor(key), 0)
  const remain = config.budgetTokens - floorTokens - scaffoldTokens - pinnedTokens

  let droppedKeys: string[]
  let trigger: ActivePlan['trigger']
  if (config.selectionMode === 'stable' && state.held !== undefined) {
    trigger = stableTrigger(state, candidates, residentTokens, config)
    if (trigger === undefined) {
      droppedKeys = state.held.dropped.filter(key => byKey.has(key))
      trigger = 'held'
    } else droppedKeys = []
  } else droppedKeys = []

  if (droppedKeys.length === 0 && !(config.selectionMode === 'stable' && trigger === 'held')) {
    const walk = candidates.filter(candidate => !hardKeep.has(candidate.messageIndex)
      && !pinnedKeys.includes(pageKey(candidate)))
    walk.sort((left, right) => right.messageIndex - left.messageIndex)
    let kept = 0
    droppedKeys = []
    for (let index = 0; index < walk.length; index++) {
      const candidate = walk[index]
      if (candidate === undefined) continue
      if (kept + candidate.tokens <= remain) kept += candidate.tokens
      else {
        droppedKeys = walk.slice(index).map(pageKey)
        break
      }
    }
    state.held = { keys: candidates.map(pageKey), dropped: droppedKeys, callsSincePlan: 0 }
  }

  const selected = droppedKeys.map(key => byKey.get(key)).filter((candidate): candidate is PageCandidate => candidate !== undefined)
  const droppedTokens = selected.reduce((sum, candidate) => sum + candidate.tokens, 0)
  if (selected.length === 0 && state.held !== undefined) {
    state.held.keys = candidates.map(pageKey)
    state.held.dropped = []
  }
  return {
    selected,
    reason: selected.length > 0 ? 'evicted' : 'fits',
    floorTokens,
    residentTokens,
    droppedTokens,
    measuredTokens,
    trigger,
  }
}

function printableArguments(value: unknown): string {
  const raw = typeof value === 'string' ? value : JSON.stringify(value) ?? ''
  const printable = [...raw].map(character => /[\p{L}\p{M}\p{N}\p{P}\p{S} ]/u.test(character) ? character : ' ').join('')
  const escaped = printable.replaceAll('[', '\\[').replaceAll(']', '\\]')
  return escaped.length > ARG_LIMIT ? `${escaped.slice(0, ARG_LIMIT)}...[truncated]` : escaped
}

/** Exact Hermes 0.13.33 recoverable stub template. */
export function buildStubText(candidate: Pick<PageCandidate, 'name' | 'args'>): string {
  const args = READ_ONLY_TOOLS.has(candidate.name) ? printableArguments(candidate.args) : 'see the call above'
  return `[ctxvm: dropped result for ${candidate.name}(${args}); re-run to restore.]`
}
