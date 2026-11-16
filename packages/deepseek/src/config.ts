/**
 * W22 — plugin configuration schema. schemastery is part of the DSH runtime and
 * is not installed outside it, so the schema is built by an injected factory:
 * the runtime entry (src/index.ts) calls makeConfig(z) with the real schemastery
 * `z` at plugin load and re-exports the result as `Config`. Tests never load this
 * module, so they run without schemastery installed (P15 option ii).
 *
 * The bundle patch inserts the row with defaults; the profile patch layer
 * overrides `config` wholesale by addressing row id `ctxvm-tracer`.
 */

type Z = typeof import('@deepseek-ai/schemastery').default

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

/** Build the Config schema from the runtime's schemastery `z` (P15 option ii). */
export function makeConfig(z: Z) {
  return z.object({
    enabled: z.boolean().default(false),
    traceDir: z.string().default('${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces'),
    tokenizerId: z.string().default('apx4-char'),
    budgetTokens: z.number().step(1).min(1).default(200_000),
    // No .required() → optional, matching schemastery's absence-is-undefined rule.
    pageSizeTokens: z.number().step(1).min(1),
    agentIdPrefix: z.string().default('dsh'),
  })
}
