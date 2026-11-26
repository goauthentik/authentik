/**
 * @file Decide whether the configured database is a dev database the server may touch.
 *   The guard judges the database the configuration actually resolves to, not the setup we expect.
 *   Every check must pass. A failed check reduces the tool set instead of refusing to start, and
 *   the reason is reported. The guard stops accidents; an agent with a shell can edit the
 *   allowlist, which is why database contents are judged too, and why allowlist changes are
 *   reported back.
 */

import { type Environment, discover } from "#dev-mcp/environment/discover";
import { allowlistChanged, suggestedAllowlist as suggest } from "#dev-mcp/guard/allowlist";
import { type Check, staticChecks } from "#dev-mcp/guard/checks";
import { databaseChecks } from "#dev-mcp/guard/signals";

export type { Check } from "#dev-mcp/guard/checks";
export { allowEntry, staticChecks } from "#dev-mcp/guard/checks";
export { licenseSignal } from "#dev-mcp/guard/signals";

export interface Verdict {
    ok: boolean;
    checks: Check[];
    allowlistChanged: boolean;
}

export const failedChecks = (verdict: Verdict) => verdict.checks.filter((c) => !c.ok);

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
        // A fix only means something for a check that failed.
        checks: checks.map(({ fix, ...check }) => (check.ok ? check : { ...check, fix })),
        allowlistChanged: allowlistChanged(env),
    };
}

/**
 * A verdict for a guard that couldn't run at all, so the reason still reaches the person.
 */
function unavailable(error: unknown): Verdict {
    return {
        ok: false,
        checks: [
            {
                name: "guard",
                ok: false,
                detail: `couldn't run: ${error instanceof Error ? error.message : String(error)}`,
                fix: "Run `make dev-status` for the full error.",
            },
        ],
        allowlistChanged: false,
    };
}

/**
 * The environment and its verdict, without throwing: a setup this can't read at all,
 * such as a git or config command that fails, becomes a failed check.
 */
export async function inspect(): Promise<{ env: Environment | null; verdict: Verdict }> {
    let env: Environment | null = null;

    try {
        env = await discover();

        return { env, verdict: await evaluate(env) };
    } catch (error) {
        return { env, verdict: unavailable(error) };
    }
}

/**
 * The local.env.yml entry that would admit this database, for the person to review.
 */
export function suggestedAllowlist(env: Environment, verdict: Verdict): string | null {
    return suggest(env, failedChecks(verdict));
}
