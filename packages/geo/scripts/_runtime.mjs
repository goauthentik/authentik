import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const PACKAGE_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const TILES_DIR = resolve(PACKAGE_DIR, "tiles");

export const IMAGE_TAG = process.env.AUTHENTIK_TILES_IMAGE ?? "authentik-tiles:dev";
export const SERVE_PORT = process.env.AUTHENTIK_TILES_PORT ?? "8484";

export function pickContainerEngine() {
    const explicit = process.env.AUTHENTIK_TILES_ENGINE;
    if (explicit) return explicit;
    return process.platform === "linux" ? "podman" : "docker";
}

export function run(command, args, options = {}) {
    return new Promise((resolvePromise, rejectPromise) => {
        const child = spawn(command, args, {
            stdio: "inherit",
            ...options,
        });
        child.on("error", rejectPromise);
        child.on("exit", (code) => {
            if (code === 0) resolvePromise();
            else rejectPromise(new Error(`${command} exited with code ${code}`));
        });
    });
}

export async function ensureImage(engine) {
    if (process.env.AUTHENTIK_TILES_SKIP_BUILD === "1") return;
    const dockerfile = resolve(PACKAGE_DIR, "Dockerfile");
    if (!existsSync(dockerfile)) {
        throw new Error(`Dockerfile not found at ${dockerfile}`);
    }
    await run(engine, ["build", "-t", IMAGE_TAG, "-f", dockerfile, PACKAGE_DIR]);
}
