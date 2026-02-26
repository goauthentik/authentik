import { $ } from "./commands.mjs";

/**
 * Checks whether the given file has uncommitted changes in git.
 *
 * @param {string} filePath
 * @param {string} [cwd]
 * @returns {Promise<{ clean: boolean, available: boolean }>}
 */
export async function gitStatus(filePath, cwd = process.cwd()) {
    return $`git status --porcelain ${filePath}`({ cwd })
        .then((output) => ({ clean: !output, available: true }))
        .catch(() => ({ clean: false, available: false }));
}

/**
 * Finds the root directory of the git repository containing the given directory.
 *
 * @param {string} cwd
 * @returns {Promise<string>} The path to the git repository root.
 * @throws {Error} If the command fails (e.g., not a git repository).
 */
export function resolveRepoRoot(cwd = process.cwd()) {
    return $`git rev-parse --show-toplevel`({ cwd });
}
