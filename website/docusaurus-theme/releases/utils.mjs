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
