/**
 * @file Utility functions for working with semantic versions.
 *
 * @runtime node
 */
import { NodeEnvironment } from "#environment/node";
import { parse } from "semver";

// ts-import-sorter: disable
import PackageJSON from "../../../../package.json" with { type: "json" };

//#region Semantic Versioning

/**
 * @typedef {`${number}.${number}.${number}${string}`} SemVerSource
 */

/**
 * The current version of authentik in SemVer format.
 *
 * @runtime node
 */
export const AuthentikVersion = /** @type {SemVerSource} */ (PackageJSON.version);

/**
 * A parsed SemVer object of the current version of authentik.
 *
 * @runtime node
 */
export const ParsedAuthentikVersion = parse(AuthentikVersion, true, true);

const { major, minor, patch } = ParsedAuthentikVersion;

//#endregion

//#region Build Identifiers

const { GIT_BUILD_HASH = "" } = process.env;

/**
 * Whether the current build is a prerelease.
 *
 * Much of the criteria that determines whether a **build** is considered a prerelease
 * is derived from environment variables -- not the SemVer version.
 *
 * Local development builds are also consider prerelease since they're not
 * necessarily tied to a specific SemVer version.
 *
 * If you're developing locally and using a Dockerized development environment,
 * Set the `GIT_BUILD_HASH` environment variable to `dev` to hint that the container should
 * prefer pre-release versioning over its own.
 */
const prerelease = NodeEnvironment === "development" || !GIT_BUILD_HASH || GIT_BUILD_HASH === "dev";

/**
 * An identifier representing the current version of authentik,
 * optionally prefixed with Git commit hash.
 *
 * This must match the behavior defined in authentik's server-side `authentik_full_version` function.
 *
 * @runtime node
 * @see {@link "authentik\_\_init\_\_.py"}
 */
export const BuildIdentifier = /** @type {SemVerSource | `${SemVerSource}+${string}`} */ (
    GIT_BUILD_HASH ? [AuthentikVersion, GIT_BUILD_HASH].join("+") : AuthentikVersion
);

//#endregion

//#region Documentation URLs

/**
 * The published subdomain for the current version of authentik.
 */
export const VersionSubdomain = /** @type {`version-${number}-${number}`} */ (
    ["version", major, minor].join("-")
);

/**
 * The published path to the current version of authentik.
 */
export const VersionPath = /** @type {`${number}.${number}`} */ ([major, minor].join("."));

/**
 * A URL to the latest pre-release documentation.
 */
export const PreReleaseDocsURL = new URL(
    process.env.PRE_RELEASE_ORIGIN || "https://next.goauthentik.io",
);

export const CurrentReleaseDocsURL = prerelease
    ? PreReleaseDocsURL
    : new URL(`https://${VersionSubdomain}.goauthentik.io`);

/**
 * A URL to the latest release notes, if any are available.
 *
 * @type {URL}
 *
 * @runtime node
 */
let ReleaseNotesURL;

if (prerelease) {
    ReleaseNotesURL = new URL("/releases", PreReleaseDocsURL);
} else {
    ReleaseNotesURL = new URL(`releases/${VersionPath}`, CurrentReleaseDocsURL);

    ReleaseNotesURL.hash = `fixed-in-${[major, minor, patch].join("")}`;
}

ReleaseNotesURL.searchParams.append("utm_source", "authentik");

export { ReleaseNotesURL };

//#endregion
