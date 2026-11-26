/**
 * @file Claude Code hooks. Each reads the hook's JSON on stdin and never blocks on its own errors.
 *   Hooks use only Node built-ins: SessionStart fires on a fresh clone, before `pnpm install`.
 */

import { existsSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { basename, join, relative } from "node:path";

import { INSTALL_HINT, isInstalled } from "#dev-mcp/optional";
import { ROOT, changedFiles } from "#dev-mcp/repo";
import { run, tail } from "#dev-mcp/run";
import { skillNames } from "#dev-mcp/skills";
import { loadCurrent, storeDir } from "#dev-mcp/store";

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
    let context =
        `authentik repo. Skills in .agents/skills: ${skillNames().join(", ")}. Load the ` +
        "matching skill before answering how-to questions. Before reporting a change done, run " +
        "the authentik-dev MCP tools (akdev_generated after model, serializer or API changes; " +
        "akdev_lint for the whole change), or `make check-gen` and `make lint-changed`. Results " +
        "list what they skipped; repeat that in your summary.";
    // The server's own dependency stands in for the whole root install.
    if (!isInstalled("@modelcontextprotocol/server")) {
        context +=
            " Dependencies aren't installed yet, so the authentik-dev MCP server and those " +
            `make targets can't run. ${INSTALL_HINT} Then restart the session.`;
    }
    emit("SessionStart", context);
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
    } else if (/^(dev-mcp|scripts\/node)\/.*\.ts$/.test(rel)) {
        commands = [["pnpm", "exec", "oxlint", "--max-warnings=0", rel]];
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
