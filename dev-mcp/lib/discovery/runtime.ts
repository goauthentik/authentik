/**
 * @file The container runtime, if any: Docker, Podman, or Podman behind a `docker` shim.
 */

import { run, which } from "#dev-mcp/run";

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
export async function portOwner(port: number): Promise<string | null> {
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
