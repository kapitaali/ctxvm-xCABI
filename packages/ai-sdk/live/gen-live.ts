/**
 * T15 B3 — LIVE drop driver for `corpus/m8`: a scripted example app driving a
 * real OpenAI-compatible free-tier provider (NVIDIA NIM by default) through
 * `streamText` while the T15 adapter (`../src`) mirrors everything into
 * `@ctxvm/node` traces — the ai-sdk analogue of T12-m2's live captures.
 *
 * SESSIONS (m2 shape, scaled to free-tier budget):
 *   echo   — read → re-read (tool_recall) → edit (2nd page) → fresh read of a
 *            second file (new contentHash, no fault) → missing-file read
 *            (error result, T6 §2: errors are not pages).
 *   thrash — 3 rounds re-reading the same 3 fixture files (9 reads): the
 *            repeats trip `tool_recall` faults through the T6 §4 matrix.
 *
 * CREDS (secret never enters this repo, the transcript, or the traces):
 *   NVIDIA_API_KEY env var — else reads /tmp/opencode/nvidia.key (0600).
 *   Optional overrides: NVIDIA_BASE_URL (default
 *   https://integrate.api.nvidia.com/v1), NVIDIA_MODEL (default
 *   meta/llama-3.3-70b-instruct), CTXVM_M8_OUT (default corpus/m8).
 *
 * Env laws: the CTXVM_* set is force-quarantined first (freshTmp law,
 * RR-UM7CAPTURE) and then armed EXPLICITLY per session — model/provider/
 * agent identity comes from this driver's own constants, never a leaked
 * environment.
 *
 * Output: <CTXVM_M8_OUT>/{live-echo,live-thrash}.{jsonl,meta.json}; per-run
 * hooks-witness stays in a throwaway scratch dir (not part of the drop).
 *
 * Run: node live/gen-live.ts
 */

for (const key of Object.keys(process.env)) {
  if (key.startsWith("CTXVM_")) delete process.env[key];
}

import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { jsonSchema, stepCountIs, streamText, tool, wrapLanguageModel } from "ai";

import { createCtxvmCapture, type FinishedCapture } from "../src/index.ts";

const HERE = fileURLToPath(new URL(".", import.meta.url));
const REPO = fileURLToPath(new URL("../../../", import.meta.url));
const OUT_DIR = process.env.CTXVM_M8_OUT ?? join(REPO, "corpus", "m8");

const MODEL_ID = process.env.NVIDIA_MODEL ?? "nvidia/nemotron-3.5-super-vl-120b-a12b";
const PROVIDER_ID = "nvidia";
const BASE_URL = process.env.NVIDIA_BASE_URL ?? "https://integrate.api.nvidia.com/v1";
const BUDGET_TOKENS = 120000;
const AGENT_ID = "ctxvm-ai-sdk";
/** NIM request extras (raw body spread via the provider's own namespace).
 *  Thinking OFF: the corpus beats are one-sentence finishes — plain-text
 *  turns match the m2/m6 precedent shape and keep per-turn token spend low.
 *  (Lane fact, verified live: thinking ON streams `reasoning_content` deltas,
 *  which this adapter passes through unmapped.) */
const NIM_BODY = { chat_template_kwargs: { enable_thinking: false } };

/** Credentials: env first, then a 0600 scratch key file. Never echoed. */
function loadApiKey(): string {
  if (process.env.NVIDIA_API_KEY) return process.env.NVIDIA_API_KEY;
  try {
    const keyPath = "/tmp/opencode/nvidia.key";
    const key = readFileSync(keyPath, "utf8").trim();
    if (key) return key;
  } catch {
    /* fallthrough to the clean error below */
  }
  console.error("B3 BLOCKED: no key — set NVIDIA_API_KEY or write /tmp/opencode/nvidia.key (the exact value, nothing else).");
  process.exit(1);
}

const apiKey = loadApiKey();
const provider = createOpenAICompatible({ name: PROVIDER_ID, baseURL: BASE_URL, apiKey });

/** Throwaway fixture workspace (redaction law: probes only, never user repos). */
function freshWorkspace(label: string): string {
  const dir = mkdtempSync(join(tmpdir(), `ctxvm-m8-${label}-`));
  const notes = join(dir, "notes");
  mkdirSync(notes, { recursive: true });
  writeFileSync(join(notes, "alpha.md"), "alpha: The quick brown fox jumps over the lazy dog.\npath: /fixture/alpha\n\n");
  writeFileSync(join(notes, "beta.md"), "beta: A hydrated terrace carries nine teal urns upright still.\npath: /fixture/beta\n\n");
  for (const name of ["a", "b", "c"]) {
    writeFileSync(join(notes, `${name}.md`), `${name}: thrash fixture line one — tea for two on a quiet dock.\n${name}-detail: /fixture/${name}\n\n`);
  }
  return dir;
}

/** Tools with real fs effects (real results → real pages, per the design). */
function fsTools(workspace: string) {
  const read = tool({
    description: "reads a file from the notes directory and returns its full content",
    inputSchema: jsonSchema<{ path: string }>({
      type: "object",
      properties: { path: { type: "string", description: "relative path, e.g. notes/alpha.md" } },
      required: ["path"],
      additionalProperties: false,
    }),
    execute: async ({ path }) => {
      try {
        const content = readFileSync(join(workspace, path), "utf8");
        return { status: "ok", path, content };
      } catch {
        // Thrown tool error → the AI SDK emits a real `tool-error` part → the
        // tap denies it (T15 §B letter / T6 §2: errors are not pages).
        throw new Error(`file not found: ${path}`);
      }
    },
  });
  const edit = tool({
    description: "appends one line to a file in the notes directory",
    inputSchema: jsonSchema<{ path: string; line: string }>({
      type: "object",
      properties: {
        path: { type: "string", description: "relative path, e.g. notes/alpha.md" },
        line: { type: "string", description: "the single line to append" },
      },
      required: ["path", "line"],
      additionalProperties: false,
    }),
    execute: async ({ path, line }) => {
      try {
        const prev = readFileSync(join(workspace, path), "utf8");
        const next = `${prev}${line}\n`;
        writeFileSync(join(workspace, path), next);
        return { status: "ok", path, bytes: next.length };
      } catch {
        // Thrown error → tool-error part → no page (T6 §2).
        throw new Error(`file not found: ${path}`);
      }
    },
  });
  return { read, edit };
}

/** The provider model, wrapped once per session through the capture middleware. */
const baseModel = provider.chatModel(MODEL_ID);
function wrappedModel(capture: ReturnType<typeof createCtxvmCapture>) {
  return wrapLanguageModel({ model: baseModel, middleware: capture.middleware });
}

interface SessionResult {
  name: string;
  finished: FinishedCapture[];
  prompts: string[];
}

async function runSession(label: string, traceName: string, prompts: string[]): Promise<SessionResult> {
  const workspace = freshWorkspace(label);
  const tools = fsTools(workspace);
  const scratch = mkdtempSync(join(tmpdir(), `ctxvm-m8-${label}-trace-`));
  process.env.CTXVM_TRACE_DIR = scratch;
  process.env.CTXVM_TRACE_NAME = traceName;

  const capture = createCtxvmCapture({
    agentId: AGENT_ID,
    // NIM's catalog id already carries the provider namespace ("nvidia/...")
    // — use it VERBATIM (m2 precedent: model string = provider-scoped id).
    model: MODEL_ID,
    provider: PROVIDER_ID,
    budgetTokens: BUDGET_TOKENS,
  });

  for (const [i, prompt] of prompts.entries()) {
    console.log(`[${label}] beat ${i + 1}/${prompts.length}: ${prompt.slice(0, 72)}`);
    const model = wrappedModel(capture);
    const result = streamText({
      model,
      tools,
      prompt,
      stopWhen: stepCountIs(8),
      temperature: 0.2,
      maxOutputTokens: 512,
      providerOptions: { nvidia: NIM_BODY },
    });
    for await (const _ of capture.tap(result.fullStream)) {} // mirror pass-over
  }

  const finished = capture.finishAll();
  if (finished.length !== 1 || !finished[0]) {
    throw new Error(`[${label}] expected 1 finished trace, got ${finished.length}`);
  }
  rmSync(workspace, { recursive: true, force: true });

  // Publish ONLY the drop files (witness stays in scratch, post-run evidence).
  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(join(OUT_DIR, `${traceName}.jsonl`), finished[0].trace.jsonl);
  const metaPath = finished[0].metaPath;
  if (!metaPath) throw new Error(`[${label}] flush did not report a meta path`);
  writeFileSync(join(OUT_DIR, `${traceName}.meta.json`), readFileSync(metaPath, "utf8"));
  rmSync(scratch, { recursive: true, force: true });

  const m = JSON.parse(readFileSync(join(OUT_DIR, `${traceName}.meta.json`), "utf8")) as {
    traceStats: { turns: number; pages: number; faults: number; residentTokens: number };
    hookStats: Record<string, number>;
    mirrorCountsAgree: boolean;
  };
  console.log(
    `[${label}] ${traceName}: ${m.traceStats.turns} turns, ${m.traceStats.pages} pages, ${m.traceStats.faults} faults, ${m.traceStats.residentTokens} resident; agree=${m.mirrorCountsAgree}`,
  );
  return { name: label, finished, prompts };
}

const ECHO_PROMPTS = [
  "Use the read tool to open notes/alpha.md, then reply with one short sentence about what the file contains.",
  "Read notes/alpha.md again, then reply with one short sentence about the second line of the file.",
  "Use the edit tool to append the line 'alpha: edited during corpus m8 capture.' to notes/alpha.md, then reply with one short sentence.",
  "Use the read tool to open notes/beta.md, then reply with one short sentence about what the file contains.",
  "Use the read tool to open notes/ghost.md, then tell me in one short sentence what happened.",
];

const THRASH_ROUNDS = 3;
const THRASH_PROMPTS = Array.from({ length: THRASH_ROUNDS }, (_v, round) =>
  `Round ${round + 1}: call the read tool three times in order — first on notes/a.md, then notes/b.md, then notes/c.md. After the third result reply with exactly: round ${round + 1} done. Do not read anything else; do not write anything.`,
);

console.log(`B3 live drop: ${MODEL_ID} @ ${BASE_URL}`);
const echo = await runSession("echo", "live-echo", ECHO_PROMPTS);
const thrash = await runSession("thrash", "live-thrash", THRASH_PROMPTS);
console.log(`\nPublished to ${OUT_DIR}: live-echo.jsonl, live-thrash.jsonl (+ meta sidecars).`);
console.log("Next: validate both traces with spec/rfc-0/validate_schema.py, then author provenance/README/checksums.");
