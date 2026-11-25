/**
 * @file Decide whether the configured database is a dev database the server may touch.
 *   The guard judges the database the configuration actually resolves to, not the setup we expect.
 *   Every check must pass. A failed check reduces the tool set instead of refusing to start, and
 *   the reason is reported. The guard stops accidents; an agent with a shell can edit the
 *   allowlist, which is why database contents are judged too, and why allowlist changes are
 *   reported back.
 */

import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import type { AllowEntry, Environment } from "./discovery.ts";
import { storeDir } from "./store.ts";

import pg from "pg";

export const DEV_DATABASE_NAMES = ["authentik", "test_authentik"];
export const USER_THRESHOLD = 50;
export const LOGIN_WINDOW_DAYS = 7;
export const SIGNALS = ["license", "users", "external_logins"] as const;

export interface Check {
    name: string;
    ok: boolean;
    detail: string;
    fix?: string;
}

export interface Verdict {
    ok: boolean;
    checks: Check[];
    allowlistChanged: boolean;
}

export const failedChecks = (verdict: Verdict) => verdict.checks.filter((c) => !c.ok);

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

/** Checks that need no database connection. */
export function staticChecks(env: Environment, environ = process.env): Check[] {
    const { config, postgres } = env;
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
    return checks;
}

const PRIVATE_RANGES = [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "127.0.0.0/8",
    "::1/128",
    "fc00::/7",
    "fe80::/10",
];

/** `<<=` (contained or equal): `::1 << ::1/128` is false. */
const EXTERNAL_LOGINS_SQL =
    "SELECT count(*) FROM authentik_events_event WHERE action = 'login' " +
    `AND created > now() - interval '${LOGIN_WINDOW_DAYS} days' AND client_ip IS NOT NULL ` +
    `AND NOT (${PRIVATE_RANGES.map((r) => `client_ip <<= inet '${r}'`).join(" OR ")})`;

const SIGNAL_SQL = {
    license: "SELECT count(*) FROM authentik_enterprise_license",
    users: "SELECT count(*) FROM authentik_core_user WHERE type IN ('internal', 'external')",
    external_logins: EXTERNAL_LOGINS_SQL,
} as const;

async function count(client: pg.Client, sql: string): Promise<number | null> {
    try {
        const res = await client.query<{ count: string }>(sql);
        return Number(res.rows[0]?.count ?? 0);
    } catch (error) {
        // 42P01: the table doesn't exist yet (an unmigrated database).
        if ((error as { code?: string }).code === "42P01") return null;
        throw error;
    }
}

/** Read-only heuristics on the database's contents: does it look like production? */
export async function databaseChecks(env: Environment): Promise<Check[]> {
    const { config } = env;
    const ignored = new Set(allowEntry(env)?.ignore_signals ?? []);
    const client = new pg.Client({
        host: String(config.pgHost.value),
        port: Number(config.pgPort.value),
        database: String(config.pgName.value),
        user: String(config.pgUser.value),
        password: config.password || undefined,
        connectionTimeoutMillis: 3_000,
        options: "-c default_transaction_read_only=on",
    });
    try {
        await client.connect();
    } catch (error) {
        return [
            {
                name: "reachable",
                ok: false,
                detail: `can't connect: ${(error as Error).message.split("\n")[0]}`,
                fix: "Start Postgres, or check the host, port and user in the resolved config.",
            },
        ];
    }
    try {
        // One connection runs one query at a time.
        const licenses = await count(client, SIGNAL_SQL.license);
        const users = await count(client, SIGNAL_SQL.users);
        const logins = await count(client, SIGNAL_SQL.external_logins);
        const signal = (name: string, tripped: boolean, detail: string): Check =>
            tripped && ignored.has(name)
                ? {
                      name: `signal_${name}`,
                      ok: true,
                      detail: `${detail} (ignored by allowlist entry)`,
                  }
                : {
                      name: `signal_${name}`,
                      ok: !tripped,
                      detail,
                      fix:
                          `If this is a dev database, add \`ignore_signals: [${name}]\` to its ` +
                          "`dev_mcp.allowed_databases` entry.",
                  };
        return [
            { name: "reachable", ok: true, detail: "connected read-only" },
            signal("license", !!licenses, `${licenses ?? 0} enterprise license(s) installed`),
            signal(
                "users",
                (users ?? 0) >= USER_THRESHOLD,
                `${users ?? 0} human users (threshold ${USER_THRESHOLD})`,
            ),
            signal(
                "external_logins",
                !!logins,
                `${logins ?? 0} logins from public addresses in the last ${LOGIN_WINDOW_DAYS} days`,
            ),
        ];
    } finally {
        await client.end();
    }
}

/**
 * Report when the allowlist differs from the last run. The person may not have read the diff
 * that changed it.
 */
function allowlistChanged(env: Environment): boolean {
    const digest = createHash("sha256")
        .update(JSON.stringify(env.config.allowedDatabases))
        .digest("hex");
    const marker = join(storeDir(), "allowlist.sha256");
    const previous = existsSync(marker) ? readFileSync(marker, "utf8").trim() : null;
    writeFileSync(marker, digest);
    return previous !== null && previous !== digest;
}

export async function evaluate(env: Environment, connect = true): Promise<Verdict> {
    const checks = staticChecks(env);
    if (connect && checks.every((c) => c.ok)) {
        checks.push(...(await databaseChecks(env)));
    } else if (connect) {
        checks.push({
            name: "database",
            ok: false,
            detail: "not checked: an earlier check failed",
        });
    }
    return {
        ok: checks.every((c) => c.ok),
        checks,
        allowlistChanged: allowlistChanged(env),
    };
}

/**
 * The local.env.yml snippet that would admit this database, for the person to review. It's
 * printed, never written: adding a database to the allowlist is the person's decision.
 */
export function suggestedAllowlist(env: Environment, verdict: Verdict): string | null {
    const failed = failedChecks(verdict);
    const signals = failed
        .filter((c) => c.name.startsWith("signal_"))
        .map((c) => c.name.slice("signal_".length));
    const remote = failed.some((c) => c.name === "connection");
    if (!signals.length && !remote) return null;
    const lines = ["dev_mcp:", "  allowed_databases:", `    - name: ${env.config.pgName.value}`];
    if (remote) lines.push(`      host: ${env.config.pgHost.value}`);
    if (signals.length) lines.push(`      ignore_signals: [${signals.join(", ")}]`);
    return lines.join("\n");
}
