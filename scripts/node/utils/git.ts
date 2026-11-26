import { $ } from "./commands.ts";

/**
 * @file Run Git plumbing without user or system configuration.
 */
const GIT_ENV: NodeJS.ProcessEnv = {
    ...process.env,
    GIT_CONFIG_GLOBAL: "/dev/null",
    GIT_CONFIG_NOSYSTEM: "1",
};

/**
 * Checks whether the given file has uncommitted changes in git.
 */
export async function gitStatus(
    filePath: string,
    cwd = process.cwd(),
): Promise<{ clean: boolean; available: boolean }> {
    return $`git status --porcelain ${filePath}`({ cwd, env: GIT_ENV })
        .then((output) => ({ clean: !output, available: true }))
        .catch(() => ({ clean: false, available: false }));
}

/**
 * Finds the root directory of the git repository containing the given directory.
 *
 * @returns The path to the git repository root.
 * @throws {Error} If the command fails (e.g., not a git repository).
 */
export function resolveRepoRoot(cwd = process.cwd()): Promise<string> {
    return $`git rev-parse --show-toplevel`({ cwd, env: GIT_ENV });
}
