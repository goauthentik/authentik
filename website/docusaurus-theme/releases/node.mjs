/**
 * @file Docusaurus release utils.
 *
 * @import { SidebarItemConfig } from "@docusaurus/plugin-content-docs/src/sidebars/types.js"
 */

import * as path from "node:path";

import FastGlob from "fast-glob";
import { coerce } from "semver";

/**
 *
 * @param {string} releasesParentDirectory
 * @returns {FastGlob.Entry[]}
 */
export function collectReleaseFiles(releasesParentDirectory) {
    const releaseFiles = FastGlob.sync("releases/**/v*.{md,mdx}", {
        cwd: releasesParentDirectory,
        onlyFiles: true,
        objectMode: true,
    })
        .map((fileEntry) => {
            return {
                ...fileEntry,
                path: fileEntry.path.replace(/\.mdx?$/, ""),
                name: fileEntry.name.replace(/^v/, "").replace(/\.mdx?$/, ""),
            };
        })
        .sort((a, b) => {
            const aSemVer = coerce(a.name);
            const bSemVer = coerce(b.name);

            if (aSemVer && bSemVer) {
                return bSemVer.compare(aSemVer);
            }

            return b.name.localeCompare(a.name);
        });

    return releaseFiles;
}

export const SUPPORTED_RELEASE_COUNT = 3;

/**
 *
 * @param {FastGlob.Entry[]} releaseFiles
 */
export function createReleaseSidebarEntries(releaseFiles) {
    /**
     * @type {SidebarItemConfig[]}
     */
    let sidebarEntries = releaseFiles.map((fileEntry) => {
        return path.join(fileEntry.path);
    });

    if (releaseFiles.length > SUPPORTED_RELEASE_COUNT) {
        // Then we add the rest of the releases as a category.
        sidebarEntries = [
            ...sidebarEntries.slice(0, SUPPORTED_RELEASE_COUNT),
            {
                type: "category",
                label: "Previous versions",
                items: sidebarEntries.slice(SUPPORTED_RELEASE_COUNT),
            },
        ];
    }

    return sidebarEntries;
}

/**
 * @typedef {object} AKReleasesPluginEnvironment
 * @property {string} [branch] The current branch name, if available.
 * e.g. "main" `version-${year}.${month}`, "feature-branch"
 * @property {string} currentReleaseOrigin The URL to the current release documentation.
 * @property {string} preReleaseOrigin The URL to the pre-release documentation.
 * @property {string} apiReferenceOrigin The URL to the API reference documentation.
 */

/**
 * Prepare the environment variables for the releases plugin.
 *
 * @returns {AKReleasesPluginEnvironment}
 */
export function prepareReleaseEnvironment() {
    return {
        branch: process.env.BRANCH,
        currentReleaseOrigin: process.env.CURRENT_RELEASE_ORIGIN || "https://docs.goauthentik.io",
        preReleaseOrigin: process.env.PRE_RELEASE_ORIGIN || "https://next.goauthentik.io",
        apiReferenceOrigin: process.env.API_REFERENCE_ORIGIN || "https://api.goauthentik.io",
    };
}
