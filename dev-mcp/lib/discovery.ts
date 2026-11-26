/**
 * @file Find out how this machine runs authentik's dev dependencies, without assuming.
 *   Contributors run Postgres in Docker, in Podman, natively, or on a dev VM. Discovery reads; it
 *   never starts, stops or installs anything. Whatever it can't classify is reported as unknown,
 *   with the raw facts it found.
 */

import { type Config, loadConfig } from "#dev-mcp/discovery/config";
import { type Postgres, classifyPostgres } from "#dev-mcp/discovery/postgres";
import { type Runtime, containerRuntime } from "#dev-mcp/discovery/runtime";
import { version } from "#dev-mcp/run";

export type { AllowEntry, Config, ConfigValue } from "#dev-mcp/discovery/config";
export type { Postgres, PostgresKind } from "#dev-mcp/discovery/postgres";
export type { Runtime, RuntimeKind } from "#dev-mcp/discovery/runtime";
export { containerRuntime } from "#dev-mcp/discovery/runtime";

export interface Environment {
    config: Config;
    runtime: Runtime;
    postgres: Postgres;
    hostTools: Record<string, string | null>;
    toolchains: Record<string, string | null>;
    /** Optional: language servers for editors and Claude Code's LSP plugins. */
    languageServers: Record<string, string | null>;
}

/** How to install each language server `discover()` looks for. */
export const LANGUAGE_SERVER_INSTALL: Record<string, string> = {
    "typescript-language-server": "npm install -g typescript-language-server typescript",
    "rust-analyzer": "rustup component add rust-analyzer",
};

export async function discover(): Promise<Environment> {
    const config = await loadConfig();
    const [runtime, postgres, psql, createdb, dropdb, uv, node, pnpm, cargo, go, make, tsls, ra] =
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
            version("typescript-language-server"),
            version("rust-analyzer"),
        ]);
    return {
        config,
        runtime,
        postgres,
        hostTools: { psql, createdb, dropdb },
        toolchains: { uv, node, pnpm, cargo, go, make },
        languageServers: { "typescript-language-server": tsls, "rust-analyzer": ra },
    };
}

/** Everything except the database password. */
export function publicEnvironment(env: Environment): Record<string, unknown> {
    const { password: _password, ...config } = env.config;
    return { ...env, config };
}
