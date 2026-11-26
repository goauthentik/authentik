/**
 * @file Guard checks that need no database connection.
 */

import type { AllowEntry, Environment } from "#dev-mcp/environment/discover";
import { composeUpFix } from "#dev-mcp/environment/services";

export const DEV_DATABASE_NAMES = ["authentik", "test_authentik"];

export interface Check {
    name: string;
    ok: boolean;
    detail: string;
    fix?: string;
}

/** The allowlist entry naming this database, matched on name and, when given, host. */
export function allowEntry(env: Environment): AllowEntry | null {
    const host = String(env.config.pgHost.value);
    const name = String(env.config.pgName.value);

    return (
        env.config.allowedDatabases.find(
            (e) => String(e.name) === name && (e.host === undefined || String(e.host) === host),
        ) ?? null
    );
}

export function staticChecks(env: Environment, environ = process.env): Check[] {
    const { config, postgres, runtime } = env;
    const entry = allowEntry(env);
    const hostListed = entry?.host !== undefined;
    const name = String(config.pgName.value);
    const token = "AUTHENTIK_TOKEN" in environ;
    const checks: Check[] = [];

    if (config.error) {
        checks.push({
            name: "config",
            ok: false,
            detail: config.error,
            fix: "Run `make install` so `uv run` works, then try again.",
        });
    }

    checks.push(
        {
            name: "debug",
            ok: config.debug.value === true,
            detail: `debug is ${JSON.stringify(config.debug.value)} (from ${config.debug.source})`,
            fix: "Run `make gen-dev-config`, or set `debug: true` in local.env.yml.",
        },
        {
            name: "connection",
            ok: postgres.local || hostListed,
            detail: `${postgres.kind}: ${postgres.detail}${hostListed ? " (allowlisted by host)" : ""}`,
            fix:
                "If this really is a dev database, list it with its host and name under " +
                "`dev_mcp.allowed_databases` in local.env.yml.",
        },
        {
            name: "database_name",
            ok: DEV_DATABASE_NAMES.includes(name) || entry !== null,
            detail: `database ${JSON.stringify(name)} (from ${config.pgName.source})`,
            fix: "Use a dev database name, or list this one under `dev_mcp.allowed_databases`.",
        },
        {
            name: "no_token",
            ok: !token,
            detail: token ? "AUTHENTIK_TOKEN is set in this shell" : "AUTHENTIK_TOKEN isn't set",
            fix:
                "Unset AUTHENTIK_TOKEN in the shell that starts the agent, or start the agent " +
                "from another shell. The server never reads it either way.",
        },
    );

    // Only with a container runtime: the fix is the compose stack. Without one, Postgres may be
    // native, and the database check says whether it answers.
    const fix = composeUpFix(runtime);

    if (fix) {
        checks.push({
            name: "running",
            ok: postgres.kind !== "down",
            detail: postgres.kind === "down" ? postgres.detail : "Postgres accepts connections",
            fix,
        });
    }

    return checks;
}
