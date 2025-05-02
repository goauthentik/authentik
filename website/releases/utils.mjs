/**
 * @file Docusaurus release utils.
 */
import FastGlob from "fast-glob";
import * as path from "node:path";

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
        .sort((a, b) => b.name.localeCompare(a.name));

    return releaseFiles;
}

export const SUPPORTED_RELEASE_COUNT = 3;

/**
 *
 * @param {FastGlob.Entry[]} releaseFiles
 */
export function createReleaseSidebarEntries(releaseFiles) {
    /**
     * @type {any[]}
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
