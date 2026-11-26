/**
 * @file The dev containers in scripts/compose.yml: PostgreSQL 18 and S3. Nothing here assumes a
 *   container runtime. With neither Docker nor Podman, there is no compose command, the guard skips
 *   its `running` check, and `akdev_services` isn't registered: a native Postgres is a supported
 *   setup too.
 */

import { run, tail } from "#dev-mcp/core/run";
import { listening } from "#dev-mcp/environment/postgres";
import type { Runtime } from "#dev-mcp/environment/runtime";
import { type Progress, noProgress } from "#dev-mcp/results/progress";
import { Result } from "#dev-mcp/results/result";

export const COMPOSE_FILE = "scripts/compose.yml";

/**
 * Named on every call: older podman-compose releases ignore `profiles` and would start the
 * `diff` service too.
 */
export const SERVICES = ["postgresql", "s3"] as const;

export type ServicesAction = "up" | "down" | "status";

const POSTGRES = { host: "127.0.0.1", port: 5432 };
const READY_TIMEOUT_MS = 60_000;

/** The compose command for `action` on this machine, or null when there's no runtime or compose. */
export function composeCommand(runtime: Runtime, action: ServicesAction): string[] | null {
    if (runtime.kind === "none" || !runtime.compose) return null;

    const base = [...runtime.compose.split(" "), "-f", COMPOSE_FILE];

    switch (action) {
        case "up":
            return [...base, "up", "-d", ...SERVICES];
        // Without `-v`: the database and S3 volumes stay, so `up` brings the same data back.
        case "down":
            return [...base, "down"];
        case "status":
            return [...base, "ps"];
    }
}

/**
 * How to bring up the dev containers, for a failed guard check. Null without a container runtime,
 * since a native Postgres is just as valid.
 */
export function composeUpFix(runtime: Runtime): string | null {
    if (runtime.kind === "none") return null;

    const engine = runtime.kind === "docker" ? "Docker" : "Podman";
    const binary = runtime.kind === "podman" ? "podman" : "docker";
    const up = `${runtime.compose ?? `${binary} compose`} -f ${COMPOSE_FILE} up -d ${SERVICES.join(" ")}`;
    const tail = "(PostgreSQL 18 on 127.0.0.1:5432, and S3), or start your own Postgres.";

    if (!runtime.running) return `Start ${engine}, then run \`${up}\` ${tail}`;

    if (!runtime.compose) {
        return `Install a compose provider for ${engine}, then run \`${up}\` ${tail}`;
    }

    return `Start the dev containers with akdev_services or \`${up}\` ${tail}`;
}

async function waitForPostgres(): Promise<boolean> {
    const deadline = Date.now() + READY_TIMEOUT_MS;

    while (Date.now() < deadline) {
        if (await listening(POSTGRES.host, POSTGRES.port)) return true;

        await new Promise((r) => setTimeout(r, 1_000));
    }

    return false;
}

export async function services(
    runtime: Runtime,
    action: ServicesAction,
    progress: Progress = noProgress,
): Promise<Result> {
    const result = new Result("akdev_services");
    const cmd = composeCommand(runtime, action);

    if (!cmd) {
        result.fail();
        result.skip(COMPOSE_FILE, "no container runtime with compose on PATH");

        return result.finish("No compose command on this machine");
    }

    const [command, ...args] = cmd;
    result.command(cmd.join(" "));

    if (!runtime.running) {
        result.fail();

        return result.finish(`${runtime.kind} isn't running; start it and try again`);
    }

    const total = action === "up" ? 2 : 1;

    progress(0, total, action === "up" ? "pulling images and starting containers" : action);

    const out = await run(command!, args, { timeoutMs: action === "up" ? 600_000 : 120_000 });
    result.data = { exit: out.code, output: tail(out, 3000) };
    result.checked.push(cmd.join(" "));

    if (out.code !== 0) {
        result.fail();

        return result.finish(`\`${cmd.join(" ")}\` exited ${out.code}`);
    }

    if (action === "up") {
        progress(1, total, "waiting for Postgres to accept connections");
        const ready = await waitForPostgres();
        progress(2, total, ready ? "Postgres is ready" : "Postgres didn't answer in time");
        result.data.postgresReady = ready;

        if (!ready) {
            result.unsure(
                "Postgres",
                `nothing listened on ${POSTGRES.host}:${POSTGRES.port} within ${READY_TIMEOUT_MS / 1000}s`,
            );
        }

        return result.finish(
            ready
                ? `Started ${SERVICES.join(" and ")}; Postgres accepts connections`
                : `Started ${SERVICES.join(" and ")}`,
        );
    }

    if (action === "down") {
        return result.finish("Stopped and removed the dev containers; their volumes are kept");
    }

    return result.finish("Listed the dev containers");
}
