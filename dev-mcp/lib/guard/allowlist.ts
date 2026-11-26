/**
 * @file The `dev_mcp.allowed_databases` allowlist: noticing when it changes, and suggesting an
 *   entry. Suggestions are printed, never written; adding a database is the person's decision.
 */

import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import type { Environment } from "#dev-mcp/discovery";
import type { Check } from "#dev-mcp/guard/checks";
import { storeDir } from "#dev-mcp/store";

/**
 * Report when the allowlist differs from the last run. The person may not have read the diff
 * that changed it.
 */
export function allowlistChanged(env: Environment): boolean {
    const digest = createHash("sha256")
        .update(JSON.stringify(env.config.allowedDatabases))
        .digest("hex");
    const marker = join(storeDir(), "allowlist.sha256");
    const previous = existsSync(marker) ? readFileSync(marker, "utf8").trim() : null;
    writeFileSync(marker, digest);
    return previous !== null && previous !== digest;
}

/** The local.env.yml entry that would admit this database, for the person to review. */
export function suggestedAllowlist(env: Environment, failed: Check[]): string | null {
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
