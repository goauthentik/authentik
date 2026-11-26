/**
 * @file Run a command and capture its output. Never throws for a failed or missing command.
 */

import { spawn } from "node:child_process";
import { accessSync, constants } from "node:fs";
import { delimiter, join } from "node:path";

import { GIT_ENV, ROOT } from "#dev-mcp/core/repo";

export interface RunResult {
    /** Exit code; 127 when the command couldn't start, 124 on timeout. */
    code: number;
    stdout: string;
    stderr: string;
}

export interface RunOptions {
    timeoutMs?: number;
    env?: NodeJS.ProcessEnv;
    cwd?: string;
    input?: string;
}

export function run(command: string, args: string[], options: RunOptions = {}): Promise<RunResult> {
    const { timeoutMs = 30_000, env, cwd = ROOT, input } = options;

    return new Promise((resolve) => {
        let stdout = "";
        let stderr = "";
        let settled = false;

        const child = spawn(command, args, {
            cwd,
            // Make targets and scripts shell out to git too, with the same config to ignore.
            env: { ...process.env, ...GIT_ENV, ...env },
            // No stdin unless there is input: a child that exits early can't break a write.
            stdio: [input === undefined ? "ignore" : "pipe", "pipe", "pipe"],
        });

        const timer = setTimeout(() => {
            child.kill("SIGTERM");
            finish({ code: 124, stdout, stderr: `${stderr}\ntimed out after ${timeoutMs}ms` });
        }, timeoutMs);

        function finish(result: RunResult) {
            if (settled) return;
            settled = true;
            clearTimeout(timer);
            resolve(result);
        }

        child.stdout?.on("data", (chunk: Buffer) => (stdout += chunk.toString()));
        child.stderr?.on("data", (chunk: Buffer) => (stderr += chunk.toString()));
        child.on("error", (error) => finish({ code: 127, stdout, stderr: error.message }));
        child.on("close", (code) => finish({ code: code ?? 1, stdout, stderr }));

        if (child.stdin) {
            // EPIPE when the child exits before reading; unhandled, it would crash the server.
            child.stdin.on("error", () => {});
            child.stdin.end(input);
        }
    });
}

/** The output a person would see: both streams, trimmed to the last `limit` characters. */
export function tail(result: RunResult, limit = 3000): string {
    return `${result.stdout}${result.stderr}`.trim().slice(-limit);
}

/** Whether `command` is on PATH. */
export function which(command: string): boolean {
    for (const dir of (process.env.PATH ?? "").split(delimiter)) {
        try {
            accessSync(join(dir, command), constants.X_OK);

            return true;
        } catch {
            // Not in this directory.
        }
    }

    return false;
}

/** The first `x.y` or `x.y.z` version in a command's output, or null if it isn't installed. */
export async function version(command: string, args = ["--version"]): Promise<string | null> {
    if (!which(command)) return null;
    const result = await run(command, args, { timeoutMs: 5_000 });

    if (result.code !== 0) return null;
    const match = /\d+\.\d+(\.\d+)?/.exec(`${result.stdout}${result.stderr}`);

    return match ? match[0] : result.stdout.trim().split("\n")[0] || null;
}

/**
 * `uv run` that never installs: plain `uv run` syncs the whole environment first, which on a fresh
 * clone means building it, about 1 GB. Without an environment the command fails, and the caller
 * reports that `make install` is needed.
 */
export const UV_RUN = ["uv", "run", "--frozen", "--no-sync"] as const;

/** Run Python in the repo's environment, from the repo root. */
export function python(args: string[], options: RunOptions = {}): Promise<RunResult> {
    const [uv, ...uvArgs] = UV_RUN;

    return run(uv, [...uvArgs, "python", ...args], options);
}
