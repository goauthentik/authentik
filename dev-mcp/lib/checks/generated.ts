/**
 * @file Are migrations, schemas, locales and API clients in step with the code?
 *   Mirrors the `test-gen` and `pending-migrations` CI jobs, through the same management commands.
 */

import { copyFileSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { genDiffPaths } from "#dev-mcp/checks/ci";
import { DEFAULT_BASE, ROOT, changedSinceBase, fingerprint } from "#dev-mcp/core/repo";
import { python, tail } from "#dev-mcp/core/run";
import { containerRuntime } from "#dev-mcp/environment/discover";
import { Result } from "#dev-mcp/results/result";

export type Regenerate = "none" | "schema";
export const SCHEMA_FILES = ["schema.yml", "blueprints/schema.json"] as const;

const DJANGO_TIMEOUT = 10 * 60_000;
// Match `make gen-build`, so the schema built here matches the one CI builds.
const GEN_ENV = { AUTHENTIK_DEBUG: "true", AUTHENTIK_OUTPOSTS__DISABLE_EMBEDDED_OUTPOST: "true" };

async function migrations(result: Result, stale: string[]): Promise<void> {
    // The same check as `ci-lint-pending-migrations`, plus --dry-run so nothing is written.
    const out = await python(["-m", "manage", "makemigrations", "--check", "--dry-run"], {
        timeoutMs: DJANGO_TIMEOUT,
    });
    if (out.code === 0) {
        result.checked.push("migrations");
    } else if (out.code === 1 && /Migrations for/.test(out.stdout)) {
        result.checked.push("migrations");
        stale.push("migrations");
        result.fail();
        result.command("make make-migrations");
        result.data.migrations = tail(out, 4000);
    } else {
        result.unsure("migrations", `makemigrations failed (exit ${out.code}): ${tail(out, 300)}`);
    }
}

function diffLines(before: string, after: string): number {
    const a = before.split("\n");
    const b = after.split("\n");
    let changed = Math.abs(a.length - b.length);
    for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) changed++;
    return changed;
}

/** Build both schemas into a temp dir with `build_schema`, then compare with the files. */
async function schemas(result: Result, stale: string[], write: boolean): Promise<boolean> {
    const dir = mkdtempSync(join(tmpdir(), "akdev-schema-"));
    const built = {
        "schema.yml": join(dir, "schema.yml"),
        "blueprints/schema.json": join(dir, "schema.json"),
    };
    try {
        const out = await python(
            [
                "-m",
                "manage",
                "build_schema",
                "--api-file",
                built["schema.yml"],
                "--blueprint-file",
                built["blueprints/schema.json"],
            ],
            { timeoutMs: DJANGO_TIMEOUT, env: GEN_ENV },
        );
        if (out.code !== 0) {
            for (const path of SCHEMA_FILES) {
                result.unsure(path, `build_schema failed (exit ${out.code}): ${tail(out, 300)}`);
            }
            return false;
        }
        let anyStale = false;
        const files = [];
        const written = [];
        for (const path of SCHEMA_FILES) {
            const next = readFileSync(built[path], "utf8");
            let current = "";
            try {
                current = readFileSync(join(ROOT, path), "utf8");
            } catch {
                // Missing counts as stale.
            }
            result.checked.push(path);
            const isStale = next !== current;
            files.push({
                path,
                stale: isStale,
                changedLines: isStale ? diffLines(current, next) : 0,
            });
            if (!isStale) continue;
            anyStale = true;
            if (write) {
                copyFileSync(built[path], join(ROOT, path));
                written.push(path);
            } else {
                stale.push(path);
                result.fail();
                result.command("make gen-build");
            }
        }
        result.data.schema = { files, written };
        return anyStale;
    } finally {
        rmSync(dir, { recursive: true, force: true });
    }
}

/**
 * Regenerating the clients needs a working `docker compose`, because the client Makefiles call it
 * by name. Phase A reports a heuristic instead of regenerating.
 */
async function clients(result: Result, schemaChanged: boolean, base: string): Promise<void> {
    const rt = await containerRuntime();
    const clients = (await genDiffPaths()).filter((p) => p.startsWith("packages/client-"));
    for (const client of clients) {
        if (schemaChanged && !changedSinceBase(client, base)) {
            let reason = "schema.yml changed but this client didn't, so it's probably stale";
            if (!rt.dockerComposeWorks) {
                reason += `; regenerating needs a working \`docker compose\` (found: ${rt.kind})`;
            }
            result.unsure(client, reason);
            result.command("make gen-clients");
        } else {
            result.checked.push(`${client} (heuristic)`);
        }
    }
}

async function locales(result: Result, stale: string[]): Promise<void> {
    const out = await python(["scripts/locales.py", "check"], { timeoutMs: 5 * 60_000 });
    result.checked.push("locales");
    if (out.code !== 0) {
        stale.push("locales");
        result.fail();
        result.command("make gen-locales");
        result.data.locales = tail(out, 2000);
    }
}

export async function checkGenerated(
    regenerate: Regenerate = "none",
    base = DEFAULT_BASE,
): Promise<Result> {
    const result = new Result("akdev_generated");
    const stale: string[] = [];
    // Each starts its own Django process; running them together roughly halves the wait.
    const [, schemaStale] = await Promise.all([
        migrations(result, stale),
        schemas(result, stale, regenerate === "schema"),
        locales(result, stale),
    ]);
    await clients(result, schemaStale || changedSinceBase("schema.yml", base), base);

    const written = (result.data.schema as { written?: string[] } | undefined)?.written ?? [];
    result.data.stale = stale;
    let headline = stale.length
        ? `Stale: ${stale.join(", ")}`
        : "Migrations, schemas and locales are up to date";
    if (written.length) headline += `. Regenerated: ${written.join(", ")}`;
    // A schema write changes the tree, so fingerprint after it.
    result.fingerprint = fingerprint();
    return result.finish(headline);
}
