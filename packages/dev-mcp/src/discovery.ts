/**
 * @file Find out how this machine runs authentik's dev dependencies, without assuming.
 *   Contributors run Postgres in Docker, in Podman, natively, or on a dev VM. Discovery reads; it
 *   never starts, stops or installs anything. Whatever it can't classify is reported as unknown,
 *   with the raw facts it found.
 */

import { lookup } from "node:dns/promises";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { isIP } from "node:net";
import { join } from "node:path";

import { ROOT } from "./repo.ts";
import { python, run, version, which } from "./run.ts";

import { parse as parseYAML } from "yaml";

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

function readYAML(path: string): Tree {
    try {
        const data = parseYAML(readFileSync(path, "utf8"));
        return data && typeof data === "object" ? (data as Tree) : {};
    } catch {
        return {};
    }
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
        error = `couldn't read authentik's config (exit ${result.code}): ${result.stderr.trim().split("\n").at(-1) ?? ""}`;
    }
    const parsed = files.map((f) => [f, readYAML(f)] as const);

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

export type RuntimeKind = "docker" | "podman" | "podman-docker-shim" | "none";

export interface Runtime {
    kind: RuntimeKind;
    running: boolean;
    /** The compose command this machine has, for commands returned to the person. */
    compose: string | null;
    /** The client Makefiles call `docker compose` by name. */
    dockerComposeWorks: boolean;
    detail: string;
}

let runtimeCache: Promise<Runtime> | null = null;

export function containerRuntime(): Promise<Runtime> {
    runtimeCache ??= detectRuntime();
    return runtimeCache;
}

async function detectRuntime(): Promise<Runtime> {
    if (which("docker")) {
        const [ver, info, compose] = await Promise.all([
            run("docker", ["--version"], { timeoutMs: 5_000 }),
            run("docker", ["info", "--format", "{{.ID}}"], { timeoutMs: 10_000 }),
            run("docker", ["compose", "version"], { timeoutMs: 5_000 }),
        ]);
        const detail = ver.stdout.trim();
        return {
            kind: detail.toLowerCase().includes("podman") ? "podman-docker-shim" : "docker",
            running: info.code === 0,
            compose: compose.code === 0 ? "docker compose" : null,
            dockerComposeWorks: compose.code === 0 && info.code === 0,
            detail,
        };
    }
    if (which("podman")) {
        const [ver, info, compose] = await Promise.all([
            run("podman", ["--version"], { timeoutMs: 5_000 }),
            run("podman", ["info", "--format", "{{.Host.Arch}}"], { timeoutMs: 10_000 }),
            run("podman", ["compose", "version"], { timeoutMs: 5_000 }),
        ]);
        return {
            kind: "podman",
            running: info.code === 0,
            compose: compose.code === 0 ? "podman compose" : null,
            dockerComposeWorks: false,
            detail: ver.stdout.trim(),
        };
    }
    return {
        kind: "none",
        running: false,
        compose: null,
        dockerComposeWorks: false,
        detail: "neither docker nor podman is on PATH",
    };
}

/** The running container that publishes `port` on this host, if any. */
async function portOwner(port: number): Promise<string | null> {
    const rt = await containerRuntime();
    if (!rt.running) return null;
    const binary = rt.kind === "podman" ? "podman" : "docker";
    const ps = await run(binary, ["ps", "--format", "{{.Names}}\t{{.Ports}}"], {
        timeoutMs: 10_000,
    });
    if (ps.code !== 0) return null;
    for (const line of ps.stdout.split("\n")) {
        const [name, ports = ""] = line.split("\t");
        if (name && ports.includes(`:${port}->`)) return name;
    }
    return null;
}

function loopbackAddress(address: string): boolean {
    if (isIP(address) === 4) return address.startsWith("127.");
    return address === "::1" || address === "::ffff:127.0.0.1";
}

export async function isLoopback(host: string): Promise<boolean> {
    if (host === "" || host === "localhost") return true;
    if (isIP(host)) return loopbackAddress(host);
    try {
        const addresses = await lookup(host, { all: true });
        return addresses.length > 0 && addresses.every((a) => loopbackAddress(a.address));
    } catch {
        return false;
    }
}

export type PostgresKind = "container" | "socket" | "local" | "remote" | "unknown";

export interface Postgres {
    kind: PostgresKind;
    local: boolean;
    container: string | null;
    detail: string;
}

export async function classifyPostgres(cfg: Config): Promise<Postgres> {
    const host = String(cfg.pgHost.value ?? "");
    const port = Number(cfg.pgPort.value);
    if (!Number.isInteger(port)) {
        return {
            kind: "unknown",
            local: false,
            container: null,
            detail: `port ${JSON.stringify(cfg.pgPort.value)} isn't a number`,
        };
    }
    if (host.startsWith("/")) {
        return { kind: "socket", local: true, container: null, detail: `Unix socket in ${host}` };
    }
    if (await isLoopback(host)) {
        const owner = await portOwner(port);
        if (owner) {
            return {
                kind: "container",
                local: true,
                container: owner,
                detail: `port ${port} is published by ${owner}`,
            };
        }
        return {
            kind: "local",
            local: true,
            container: null,
            detail:
                `${host}:${port}, not published by a running container this machine can see ` +
                "(a native service, or a runtime discovery doesn't know)",
        };
    }
    return {
        kind: "remote",
        local: false,
        container: null,
        detail: `${host}:${port} isn't on this machine`,
    };
}

export interface Environment {
    config: Config;
    runtime: Runtime;
    postgres: Postgres;
    hostTools: Record<string, string | null>;
    toolchains: Record<string, string | null>;
}

export async function discover(): Promise<Environment> {
    const config = await loadConfig();
    const [runtime, postgres, psql, createdb, dropdb, uv, node, pnpm, cargo, go, make] =
        await Promise.all([
            containerRuntime(),
            classifyPostgres(config),
            version("psql"),
            version("createdb"),
            version("dropdb"),
            version("uv"),
            version("node"),
            version("pnpm"),
            version("cargo"),
            version("go", ["version"]),
            version("make"),
        ]);
    return {
        config,
        runtime,
        postgres,
        hostTools: { psql, createdb, dropdb },
        toolchains: { uv, node, pnpm, cargo, go, make },
    };
}

/** Everything except the database password. */
export function publicEnvironment(env: Environment): Record<string, unknown> {
    const { password: _password, ...config } = env.config;
    return { ...env, config };
}
