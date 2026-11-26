/**
 * @file Read-only heuristics on the database's contents: does it look like production?
 */

import type { Environment } from "#dev-mcp/environment/discover";
import { type Check, allowEntry } from "#dev-mcp/guard/checks";
import { isDevTestLicense, verifyLicense } from "#dev-mcp/guard/license";
import { missing, notInstalled } from "#dev/lib/optional";

import type { Client } from "pg";

export const USER_THRESHOLD = 50;
export const LOGIN_WINDOW_DAYS = 7;
export const SIGNALS = ["license", "users", "external_logins"] as const;

/**
 * Keep in step with `E2E_ATTRIBUTE` in web/e2e/fixtures/FormFixture.ts.
 */
export const E2E_ATTRIBUTE = "goauthentik.io/testing/e2e";

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
    // The e2e suite tags what it creates, and those users accumulate in dev databases by design.
    users:
        "SELECT count(*) FROM authentik_core_user WHERE type IN ('internal', 'external') " +
        `AND NOT attributes @> '{"${E2E_ATTRIBUTE}": true}'::jsonb`,
    external_logins: EXTERNAL_LOGINS_SQL,
} as const;

/**
 * 42P01: the table doesn't exist yet (an unmigrated database).
 */
const isUndefinedTable = (error: unknown) => (error as { code?: string }).code === "42P01";

async function count(client: Client, sql: string): Promise<number | null> {
    try {
        const res = await client.query<{ count: string }>(sql);

        return Number(res.rows[0]?.count ?? 0);
    } catch (error) {
        if (isUndefinedTable(error)) return null;
        throw error;
    }
}

/** Installed license keys, or null when the table doesn't exist yet. */
async function licenseKeys(client: Client): Promise<string[] | null> {
    try {
        const res = await client.query<{ key: string }>(
            "SELECT key FROM authentik_enterprise_license",
        );

        return res.rows.map((r) => r.key);
    } catch (error) {
        if (isUndefinedTable(error)) return null;
        throw error;
    }
}

/**
 * The license signal fires when any installed license lacks a verified `dev_test` claim. A
 * license authentik's licensing CA issued for development and testing is evidence of a dev
 * database; any other license, or one whose signature doesn't verify, is treated as production.
 */
export function licenseSignal(
    keys: string[] | null,
    root?: Buffer,
): { tripped: boolean; detail: string } {
    if (!keys?.length) return { tripped: false, detail: "no enterprise license installed" };
    const checks = keys.map((key) => verifyLicense(key, root));
    const dev = checks.filter(isDevTestLicense).length;

    if (dev === keys.length) {
        return {
            tripped: false,
            detail: `${keys.length} enterprise license(s), all verified dev_test licenses`,
        };
    }

    const unverified = checks
        .map((c) => (c.verified ? null : c.reason))
        .filter((r): r is string => r !== null);

    let detail = `${keys.length} enterprise license(s), ${keys.length - dev} without a verified dev_test claim`;

    if (unverified.length) detail += ` (${[...new Set(unverified)].join("; ")})`;

    return { tripped: true, detail };
}

export async function databaseChecks(env: Environment): Promise<Check[]> {
    const pg = await import("pg").catch(missing);

    if (!pg) {
        return [
            {
                name: "reachable",
                ok: false,
                detail: `can't check the database: ${notInstalled("pg")}`,
            },
        ];
    }

    const { config } = env;
    const ignored = new Set(allowEntry(env)?.ignore_signals ?? []);

    const client = new pg.default.Client({
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
        const license = licenseSignal(await licenseKeys(client));
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
            signal("license", license.tripped, license.detail),
            signal(
                "users",
                (users ?? 0) >= USER_THRESHOLD,
                `${users ?? 0} human users, not counting e2e test users (threshold ${USER_THRESHOLD})`,
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
