/**
 * @file Utility functions for working with semantic versions.
 *
 * @runtime common
 */

/**
 * Creates a URL to the release notes for the given version.
 *
 * @param {string} semver
 * @returns {URL}
 * @runtime common
 */
export function createReleaseNotesURL(semver) {
    const segments = semver.split(".");
    const versionFamily = segments.slice(0, -1).join(".");

    const release = `${versionFamily}#fixed-in-${segments.join("")}`;

    return new URL(`/docs/releases/${release}`, "https://goauthentik.io");
}
