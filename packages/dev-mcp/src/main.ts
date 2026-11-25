#!/usr/bin/env node
/**
 * @file authentik-dev: a local MCP server and checks for authentik contributors.
 *   Usage:
 *   main.ts serve                       Run the MCP server over stdio.
 *   main.ts status [--json]             Show environment discovery and the database guard.
 *   main.ts check-gen [--json] [--regenerate schema] [--base <ref>]
 *   main.ts lint-changed [--json] [--fix] [--base <ref>] [paths...]
 *   main.ts hook <session-start|post-edit|stop>
 *   Exit codes:
 *   0  Passed
 *   1  A check failed, or couldn't tell
 *   2  The database guard refused the database
 */

import { parseArgs } from "node:util";

import { checkGenerated, type Regenerate } from "./checks/generated.ts";
import { lint } from "./checks/lint.ts";
import { discover, publicEnvironment } from "./discovery.ts";
import { evaluate, failedChecks, suggestedAllowlist } from "./guard.ts";
import { HOOKS, type HookName, runHook } from "./hooks.ts";
import { DEFAULT_BASE } from "./repo.ts";
import type { Result } from "./result.ts";
import { serve } from "./server.ts";
import { save } from "./store.ts";

function print(result: Result, json: boolean): number {
    console.log(json ? JSON.stringify(result, null, 2) : result.toText());
    return result.ok && !result.unknown.length ? 0 : 1;
}

async function status(json: boolean): Promise<number> {
    const env = await discover();
    const verdict = await evaluate(env);
    if (json) {
        console.log(
            JSON.stringify({ environment: publicEnvironment(env), guard: verdict }, null, 2),
        );
        return verdict.ok ? 0 : 1;
    }
    const { postgres, runtime, config } = env;
    console.log(`Postgres: ${postgres.kind} (${postgres.detail})`);
    console.log(`Containers: ${runtime.kind}, compose: ${runtime.compose ?? "none"}`);
    console.log(`Config files: ${config.files.join(", ") || "none"}`);
    for (const check of verdict.checks) {
        console.log(`  ${check.ok ? "ok  " : "FAIL"} ${check.name}: ${check.detail}`);
        if (!check.ok && check.fix) console.log(`       ${check.fix}`);
    }
    if (verdict.allowlistChanged)
        console.log("Note: the database allowlist changed since the last run.");
    const snippet = suggestedAllowlist(env, verdict);
    if (snippet)
        console.log(`\nIf this is your dev database, add this to local.env.yml:\n\n${snippet}`);
    return verdict.ok ? 0 : 1;
}

async function checkGen(json: boolean, regenerate: Regenerate, base: string): Promise<number> {
    const verdict = await evaluate(await discover());
    if (!verdict.ok) {
        const failed = failedChecks(verdict)
            .map((c) => `${c.name}: ${c.detail}`)
            .join("; ");
        console.error(`Refusing to touch this database. ${failed}`);
        console.error("Run `make dev-status` for details.");
        return 2;
    }
    const result = await checkGenerated(regenerate, base);
    save("generated", result);
    return print(result, json);
}

async function main(argv: string[]): Promise<number> {
    const { values, positionals } = parseArgs({
        args: argv,
        allowPositionals: true,
        options: {
            json: { type: "boolean", default: false },
            fix: { type: "boolean", default: false },
            regenerate: { type: "string", default: "none" },
            base: { type: "string", default: DEFAULT_BASE },
        },
    });
    const [command, ...rest] = positionals;
    switch (command) {
        case "serve":
            await serve();
            return -1;
        case "status":
            return status(values.json);
        case "check-gen":
            return checkGen(
                values.json,
                values.regenerate === "schema" ? "schema" : "none",
                values.base,
            );
        case "lint-changed": {
            const result = await lint(rest, values.base, values.fix);
            save("lint", result);
            return print(result, values.json);
        }
        case "hook":
            if (rest[0] && rest[0] in HOOKS) return runHook(rest[0] as HookName);
            console.error(`Unknown hook. Expected one of: ${Object.keys(HOOKS).join(", ")}`);
            return 2;
        default:
            console.error("Usage: main.ts <serve|status|check-gen|lint-changed|hook> [options]");
            return 2;
    }
}

const code = await main(process.argv.slice(2));
// `serve` keeps running until stdin closes.
if (code >= 0) process.exit(code);
