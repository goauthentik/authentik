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
 *   2  The database guard refused the database, or bad usage
 *   Each command loads its own modules, so the hooks and `status` work before `pnpm install`.
 */

import { parseArgs } from "node:util";

import type { Result } from "#dev-mcp/results/result";
import { save } from "#dev-mcp/results/store";
import { DEFAULT_BASE } from "#dev/lib/git";
import { INSTALL_HINT, delegateImportError } from "#dev/lib/optional";

const HOOK_NAMES = ["session-start", "post-edit", "stop"] as const;

type HookName = (typeof HOOK_NAMES)[number];

function print(result: Result, json: boolean): number {
    console.log(json ? JSON.stringify(result, null, 2) : result.toText());

    return result.ok && !result.unknown.length ? 0 : 1;
}

async function status(json: boolean): Promise<number> {
    const { LANGUAGE_SERVER_COMMANDS: LANGUAGE_SERVER_INSTALL, publicEnvironment } =
        await import("#dev-mcp/environment/discover");

    const { inspect, suggestedAllowlist } = await import("#dev-mcp/guard/verdict");
    const { env, verdict } = await inspect();

    if (json) {
        const environment = env && publicEnvironment(env);

        console.log(JSON.stringify({ environment, guard: verdict }, null, 2));

        return verdict.ok ? 0 : 1;
    }

    if (env) {
        const { postgres, runtime, config } = env;

        console.log(`Postgres: ${postgres.kind} (${postgres.detail})`);
        console.log(`Containers: ${runtime.kind}, compose: ${runtime.compose ?? "none"}`);
        console.log(`Config files: ${config.files.join(", ") || "none"}`);
    }

    for (const check of verdict.checks) {
        console.log(`  ${check.ok ? "ok  " : "FAIL"} ${check.name}: ${check.detail}`);

        if (!check.ok && check.fix) console.log(`       ${check.fix}`);
    }

    if (verdict.allowlistChanged) {
        console.log("Note: the database allowlist changed since the last run.");
    }

    const absent = Object.entries(env?.languageServers ?? {}).filter(([, v]) => v === null);

    if (absent.length) {
        console.log("\nOptional, for editors and Claude Code's LSP plugins:");

        for (const [name] of absent) {
            console.log(`  ${name} isn't installed: ${LANGUAGE_SERVER_INSTALL[name]}`);
        }
    }

    const snippet = env && suggestedAllowlist(env, verdict);

    if (snippet) {
        console.log(`\nIf this is your dev database, add this to local.env.yml:\n\n${snippet}`);
    }

    return verdict.ok ? 0 : 1;
}

async function checkGen(json: boolean, regenerate: "none" | "schema", base: string) {
    const { failedChecks, inspect } = await import("#dev-mcp/guard/verdict");
    const { verdict } = await inspect();

    if (!verdict.ok) {
        const failed = failedChecks(verdict)
            .map((c) => `${c.name}: ${c.detail}`)
            .join("; ");

        console.error(`Refusing to touch this database. ${failed}`);
        console.error("Run `make dev-status` for details.");

        return 2;
    }

    const { checkGenerated } = await import("#dev-mcp/checks/generated");
    const result = await checkGenerated(regenerate, base);
    save("generated", result);

    return print(result, json);
}

async function lintChanged(paths: string[], base: string, fix: boolean) {
    const { lint } = await import("#dev-mcp/checks/lint");
    const result = await lint(paths, base, fix);
    save("lint", result);

    return result;
}

async function serve(): Promise<number> {
    const server = await import("#dev-mcp/server/serve").catch(delegateImportError);

    if (!server) {
        const { NO_FALLBACK, serveFallback } = await import("#dev-mcp/server/fallback");

        // The real server started by the fallback: don't nest another fallback inside it.
        if (process.env[NO_FALLBACK]) {
            console.error(
                `authentik-dev can't start: its dependencies aren't installed. ${INSTALL_HINT}`,
            );

            return 1;
        }

        serveFallback();

        return -1;
    }

    // Its checks run make and pnpm: give them an nvm Node that fits when the active one doesn't.
    const { chooseNode, withNode } = await import("#dev-mcp/environment/node");
    process.env.PATH = withNode(process.env, chooseNode()).PATH;

    await server.serve();

    // Keeps running until stdin closes.
    return -1;
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
            return serve();
        case "status":
            return status(values.json);
        case "check-gen":
            return checkGen(
                values.json,
                values.regenerate === "schema" ? "schema" : "none",
                values.base,
            );
        case "lint-changed":
            return print(await lintChanged(rest, values.base, values.fix), values.json);
        case "hook": {
            const name = rest[0] as HookName;

            if (!HOOK_NAMES.includes(name)) {
                console.error(`Unknown hook. Expected one of: ${HOOK_NAMES.join(", ")}`);

                return 2;
            }

            const { runHook } = await import("#dev-mcp/agent/hooks");

            return runHook(name);
        }
        default:
            console.error("Usage: main.ts <serve|status|check-gen|lint-changed|hook> [options]");
            return 2;
    }
}

const code = await main(process.argv.slice(2));

if (code >= 0) process.exit(code);
