/**
 * W22 — plugin configuration schema (schemastery `z`, the DSH convention:
 *   import z from '@deepseek-ai/schemastery'
 *   export const Config: z<Config> = z.object({ ... })
 * The bundle patch inserts the row with defaults; the profile patch layer
 * overrides `config` wholesale by addressing row id `ctxvm-tracer`.
 *
 * schemastery is part of the DSH runtime and may not be available outside
 * DSH (e.g. in tests). Config is loaded lazily; call setConfig() with the
 * schemastery `z` value from the DSH runtime before accessing Config.
 */

let _Config: any = null

/** Inject the schemastery schema (called by the DSH runtime at load time). */
export function setConfig(z: any): void {
  if (_Config) return
  _Config = z.object({
    enabled: z.boolean().default(false),
    traceDir: z.string().default('${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces'),
    tokenizerId: z.string().default('apx4-char'),
    budgetTokens: z.number().step(1).min(1).default(200_000),
    pageSizeTokens: z.number().step(1).min(1),
    agentIdPrefix: z.string().default('dsh'),
  })
}

/** Read the lazily-loaded config schema (null until setConfig has been called). */
export function getConfig(): any {
  return _Config
}

export interface CtxvmDshConfig {
  /** Master switch. Mirror-mode capture runs only when true. */
  enabled: boolean
  /** Trace output directory. Default follows XDG state (private, 0700). */
  traceDir: string
  /** Tokenizer unit id passed to @ctxvm/node (default estimate apx4-char). */
  tokenizerId: string
  /** Declared page budget (drives turn.render headroom bookkeeping). */
  budgetTokens: number
  /** Reserved for Phase 3 stub sizing; inert in mirror mode. */
  pageSizeTokens?: number
  /** agentId prefix: agentId = `${agentIdPrefix}:${sessionId prefix}`. */
  agentIdPrefix: string
}

/** Config schema (null until setConfig has been called with schemastery `z`). */
export const Config: any = null
