/**
 * @file authentik's resolved configuration, and where each value came from.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { missing } from "#dev-mcp/core/optional";
import { ROOT } from "#dev-mcp/core/repo";
import { python } from "#dev-mcp/core/run";

export interface ConfigValue {
    value: unknown;
    source: string;
}

export interface AllowEntry {
    name?: string;
    host?: string;
    ignore_signals?: string[];
}

export interface Config {
    debug: ConfigValue;
    pgHost: ConfigValue;
    pgPort: ConfigValue;
    pgName: ConfigValue;
    pgUser: ConfigValue;
    files: string[];
    allowedDatabases: AllowEntry[];
    /** Never included in any output. */
    password: string;
    error: string | null;
}

type Tree = Record<string, unknown>;

function at(tree: unknown, path: string): unknown {
    let node = tree;
    for (const part of path.split(".")) {
        if (node === null || typeof node !== "object") return undefined;
        node = (node as Tree)[part];
    }
    return node;
}

/** The config files authentik's loader reads, in its order (see `SEARCH_PATHS`). */
export function configFiles(): string[] {
    const env = process.env.AUTHENTIK_ENV ?? "local";
    const files = [join(ROOT, "authentik/lib/default.yml"), "/etc/authentik/config.yml"];
    files.push(...[".yml", ".env.yml", ".yaml", ".env.yaml"].map((ext) => join(ROOT, env + ext)));
    try {
        for (const f of readdirSync("/etc/authentik/config.d")) {
            if (f.endsWith(".yml")) files.push(join("/etc/authentik/config.d", f));
        }
    } catch {
        // No config.d.
    }
    return files.filter((f) => existsSync(f));
}

const display = (file: string) =>
    file.startsWith(`${ROOT}/`) ? file.slice(ROOT.length + 1) : file;

/** Each config file's contents, for attributing values. Empty without the `yaml` package. */
async function readFiles(files: string[]): Promise<(readonly [string, Tree])[]> {
    const yaml = await import("yaml").catch(missing);
    return files.map((file) => {
        try {
            const data: unknown = yaml?.parse(readFileSync(file, "utf8"));
            return [file, data && typeof data === "object" ? (data as Tree) : {}] as const;
        } catch {
            return [file, {}] as const;
        }
    });
}

/**
 * Resolve config through authentik's own loader, so files, `AUTHENTIK_*` variables and defaults
 * resolve exactly as `ak` resolves them.
 */
export async function loadConfig(): Promise<Config> {
    const files = configFiles();
    const result = await python(["-m", "authentik.lib.config"], { timeoutMs: 60_000 });
    let tree: Tree = {};
    let error: string | null = null;
    try {
        tree = JSON.parse(result.stdout) as Tree;
    } catch {
        const reason = result.stderr.trim().split("\n").at(-1) ?? "";
        error = `couldn't read authentik's config (exit ${result.code}): ${reason}`;
    }
    const parsed = await readFiles(files);

    function resolved(path: string, fallback: unknown): ConfigValue {
        const envName = `AUTHENTIK_${path.toUpperCase().replaceAll(".", "__")}`;
        let source = "built-in default";
        for (const [file, data] of parsed) {
            if (at(data, path) !== undefined) source = display(file);
        }
        if (envName in process.env) source = `$${envName}`;
        const value = at(tree, path);
        return { value: value === undefined ? fallback : value, source };
    }

    const allowed = at(tree, "dev_mcp.allowed_databases");
    return {
        debug: resolved("debug", false),
        pgHost: resolved("postgresql.host", "localhost"),
        pgPort: resolved("postgresql.port", 5432),
        pgName: resolved("postgresql.name", "authentik"),
        pgUser: resolved("postgresql.user", "authentik"),
        files: files.map(display),
        allowedDatabases: Array.isArray(allowed)
            ? allowed.filter((a): a is AllowEntry => !!a && typeof a === "object")
            : [],
        password: String(at(tree, "postgresql.password") ?? ""),
        error,
    };
}
