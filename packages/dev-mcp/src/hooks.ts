/**
 * @file Claude Code hooks. Each reads the hook's JSON on stdin and never blocks on its own errors.
 */

import { existsSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { basename, join, relative } from "node:path";

import { ROOT, changedFiles } from "./repo.ts";
import { run, tail } from "./run.ts";
import { listSkills } from "./skills.ts";
import { loadCurrent, storeDir } from "./store.ts";

const GENERATED_TRIGGERS = ["models.py", "serializers.py", "api.py", "urls.py", "views.py"];

interface HookInput {
    session_id?: string;
    stop_hook_active?: boolean;
    tool_input?: { file_path?: string };
}

function emit(event: string, context: string): void {
    process.stdout.write(
        `${JSON.stringify({ hookSpecificOutput: { hookEventName: event, additionalContext: context } })}\n`,
    );
}

function sessionStart(): void {
    const names = listSkills()
        .map((s) => s.name)
        .join(", ");
    emit(
        "SessionStart",
        `authentik repo. Skills in .agents/skills: ${names}. Load the matching skill before ` +
            "answering how-to questions. Before reporting a change done, run the authentik-dev " +
            "MCP tools (akdev_generated after model, serializer or API changes; akdev_lint for " +
            "the whole change), or `make check-gen` and `make lint-changed`. Results list what " +
            "they skipped; repeat that in your summary.",
    );
}

async function lintFile(rel: string): Promise<string | null> {
    let commands: string[][] = [];
    if (rel.endsWith(".py")) {
        commands = [
            ["uv", "run", "--frozen", "ruff", "check", rel],
            ["uv", "run", "--frozen", "black", "--check", "-q", rel],
        ];
    } else if (rel.startsWith("web/") && /\.(ts|js|css)$/.test(rel)) {
        commands = [["pnpm", "--dir", "web", "exec", "oxlint", "--max-warnings=0", rel.slice(4)]];
    } else if (rel.startsWith("packages/dev-mcp/") && rel.endsWith(".ts")) {
        commands = [
            [
                "pnpm",
                "--dir",
                "packages/dev-mcp",
                "exec",
                "oxlint",
                "--max-warnings=0",
                rel.slice(17),
            ],
        ];
    }
    const problems = [];
    for (const [cmd, ...args] of commands) {
        const out = await run(cmd!, args, { timeoutMs: 60_000 });
        if (out.code !== 0) problems.push(`$ ${[cmd, ...args].join(" ")}\n${tail(out, 1500)}`);
    }
    return problems.length ? problems.join("\n") : null;
}

async function postEdit(input: HookInput): Promise<void> {
    const raw = input.tool_input?.file_path;
    if (!raw || !existsSync(raw)) return;
    const rel = relative(ROOT, realpathSync(raw));
    if (rel.startsWith("..")) return;
    const notes = [];
    const findings = await lintFile(rel);
    if (findings) notes.push(`Lint findings in ${rel}:\n${findings}`);
    if (rel.startsWith("authentik/") && GENERATED_TRIGGERS.includes(basename(rel))) {
        notes.push(
            "This file can change migrations, schema.yml or the API clients. Run " +
                "akdev_generated (or `make check-gen`) before reporting the change done.",
        );
    }
    if (notes.length) emit("PostToolUse", notes.join("\n\n"));
}

/** Block once per session if Django code changed and generated files weren't checked. */
function stop(input: HookInput): void {
    if (input.stop_hook_active) return;
    const session = String(input.session_id ?? "");
    const marker = join(storeDir(), "stop-blocked");
    const blocked = new Set(existsSync(marker) ? readFileSync(marker, "utf8").split("\n") : []);
    if (blocked.has(session)) return;
    if (!changedFiles().some((p) => p.startsWith("authentik/") && p.endsWith(".py"))) return;
    if (loadCurrent("generated")) return;
    blocked.add(session);
    writeFileSync(marker, [...blocked].filter(Boolean).slice(-200).join("\n"));
    process.stdout.write(
        `${JSON.stringify({
            decision: "block",
            reason:
                "Python under authentik/ changed and generated files haven't been checked " +
                "against the current tree. Run akdev_generated (or `make check-gen`) and include " +
                "its result, including anything it skipped, in your summary.",
        })}\n`,
    );
}

export const HOOKS = { "session-start": sessionStart, "post-edit": postEdit, stop };
export type HookName = keyof typeof HOOKS;

export async function runHook(name: HookName): Promise<number> {
    try {
        const raw = readFileSync(0, "utf8");
        await HOOKS[name](raw.trim() ? (JSON.parse(raw) as HookInput) : {});
    } catch {
        // A broken hook must never block a session or an edit.
    }
    return 0;
}
