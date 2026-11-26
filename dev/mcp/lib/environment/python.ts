/**
 * @file Python in the repo's uv environment, without ever installing it.
 */

import { type RunOptions, type RunResult, run } from "#dev/lib/process";

/**
 * Run `uv` without syncing the environment; callers can report when setup is required.
 */
export const UV_RUN = ["uv", "run", "--frozen", "--no-sync"] as const;

/**
 * Run Python in the repo's environment, from the repo root.
 */
export function python(args: string[], options: RunOptions = {}): Promise<RunResult> {
    const [uv, ...uvArgs] = UV_RUN;

    return run(uv, [...uvArgs, "python", ...args], options);
}
