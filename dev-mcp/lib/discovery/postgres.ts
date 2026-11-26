/**
 * @file Where the configured database lives, as far as this machine can tell.
 */

import { lookup } from "node:dns/promises";
import { isIP } from "node:net";

import type { Config } from "#dev-mcp/discovery/config";
import { portOwner } from "#dev-mcp/discovery/runtime";

export type PostgresKind = "container" | "socket" | "local" | "remote" | "unknown";

export interface Postgres {
    kind: PostgresKind;
    local: boolean;
    container: string | null;
    detail: string;
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
