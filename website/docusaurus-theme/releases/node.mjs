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
 * Collect all Markdown files from the releases directory.
 *
 * @param {string} releasesParentDirectory
 * @returns {AKReleaseFile[]}
 */
export function collectReleaseFiles(releasesParentDirectory) {
    /**
     * @type {Array<FastGlob.Entry & AKReleaseFile>}
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

    const [latestRelease] = releaseFiles;

    if (latestRelease) {
        const extension = extname(latestRelease.dirent.name);

        const fileContent = readFileSync(
            join(releasesParentDirectory, `${latestRelease.path}${extension}`),
            "utf-8",
        );

        const { frontMatter } = parseFileContentFrontMatter(fileContent);

        latestRelease.frontMatter = frontMatter;
    }

    return releaseFiles;
}

export const SUPPORTED_RELEASE_COUNT = 3;

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
