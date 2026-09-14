import { $ } from "./commands.ts";

/**
 * Checks whether the given file has uncommitted changes in git.
 */
export async function gitStatus(
    filePath: string,
    cwd = process.cwd(),
): Promise<{ clean: boolean; available: boolean }> {
    return $`git status --porcelain ${filePath}`({ cwd })
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
    return $`git rev-parse --show-toplevel`({ cwd });
}
