/**
 * @file Docusaurus release utils.
 *
 * @import { SidebarItemConfig } from "@docusaurus/plugin-content-docs/src/sidebars/types.js"
 * @import { AKReleaseFile, AKReleasesPluginEnvironment } from "./common.mjs"
 */

import { readFileSync } from "node:fs";
import { extname, join } from "node:path";

import { parseFileContentFrontMatter } from "@docusaurus/utils/lib/markdownUtils.js";
import FastGlob from "fast-glob";
import { coerce } from "semver";

/**
 * Number of supported releases to show in the sidebar.
 */
export const SUPPORTED_RELEASE_COUNT = 3;

/**
 * @typedef {FastGlob.Entry & AKReleaseFile} AKReleaseFileEntry
 */

/**
 * Reads and parses the front matter of recent release files.
 *
 * @param {string} releasesParentDirectory
 * @param {AKReleaseFileEntry} release
 * @param {number} index
 */
function parseRelease(releasesParentDirectory, release, index) {
    if (index > SUPPORTED_RELEASE_COUNT - 1) {
        return release;
    }

    const extension = extname(release.dirent.name);

    const fileContent = readFileSync(
        join(releasesParentDirectory, `${release.path}${extension}`),
        "utf-8",
    );

    const { frontMatter } = parseFileContentFrontMatter(fileContent);

    if (frontMatter.beta) {
        release.name += " (Release Candidate)";
    }

    return {
        ...release,
        frontMatter,
    };
}

/**
 * Collect all Markdown files from the releases directory.
 *
 * @param {string} releasesParentDirectory
 * @returns {AKReleaseFile[]}
 */
export function collectReleaseFiles(releasesParentDirectory) {
    /**
     * @type {AKReleaseFileEntry[]}
     */
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

    const parsedReleaseFiles = releaseFiles.map((release, index) =>
        parseRelease(releasesParentDirectory, release, index),
    );

    return parsedReleaseFiles;
}

/**
 *
 * @param {AKReleaseFile[]} releaseFiles
 */
export function createReleaseSidebarEntries(releaseFiles) {
    /**
     * @type {SidebarItemConfig[]}
     */
    let sidebarEntries = releaseFiles.map((fileEntry) => {
        return {
            type: "doc",
            id: fileEntry.path,
            label: fileEntry.name,
            key: `release-${fileEntry.name}`,
        };
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
