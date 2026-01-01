/**
 * @file Version Utilities
 */

/**
 * Default support duration: 2 years in milliseconds.
 */
export const DEFAULT_VERSION_SUPPORT_DURATION = 2 * 365 * 24 * 60 * 60 * 1000;

/**
 * A validation error indicating the version is invalid.
 */
export class VersionValidationError extends Error {}

/**
 * @throws {Error} if the version is older than 2 years
 *
 * @param {import("semver").SemVer} parsed Parsed semver version
 * @param {number} [supportDuration] Milliseconds cutoff
 */
export function assertVersionSupported(parsed, supportDuration = DEFAULT_VERSION_SUPPORT_DURATION) {
    const versionDate = new Date(parsed.major, parsed.minor - 1);
    const now = new Date();

    if (now.getTime() - versionDate.getTime() >= supportDuration) {
        const message = `Semver version ${versionDate.getFullYear()}.${versionDate.getMonth()} is older than 2 years`;

        throw new VersionValidationError(message);
    }
}
