export const YEAR_MS = 2 * 360 * 24 * 60 * 60 * 1000;

/**
 * @param {import("semver").SemVer} parsed
 */
export function validateVersion(parsed) {
    const versionDate = new Date(parsed.major, parsed.minor - 1);
    const now = new Date();

    if (now.getTime() - versionDate.getTime() >= YEAR_MS) {
        throw new Error(
            `Semver version ${versionDate.getFullYear()}.${versionDate.getMonth()} is older than 2 years`,
        );
    }
}
