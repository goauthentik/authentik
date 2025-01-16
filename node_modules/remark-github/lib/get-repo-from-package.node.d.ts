/**
 * Get the repository from `package.json`.
 *
 * @param {string} cwd
 *   CWD.
 * @returns {string | undefined}
 *   Repository.
 */
export function getRepoFromPackage(cwd: string): string | undefined;
export type PackageJson = import('type-fest').PackageJson;
