/**
 * @file Docusaurus redirects utils.
 */

import { parseAllRedirects } from "netlify-redirect-parser";

/**
 * @typedef {Object} RedirectEntry
 *
 * @property {string} from
 * @property {string} to
 * @property {boolean} force
 */

/**
 * Given a pathname, return a RegExp that matches the pathname.
 *
 * @param {string} pathname
 * @returns {RegExp}
 */
export function pathnameToMatcher(pathname) {
    return new RegExp("^" + pathname.replace(/\*/g, "(?<splat>.*)").replace(/\//g, "\\/"), "i");
}

/**
 * Given a destination, return a RegExp that matches the destination.
 *
 * This is used to match the inverse of a pathname matcher.
 * @param {string} destination
 * @returns {RegExp}
 */
export function destinationToMatcher(destination) {
    return new RegExp(
        "^" + destination.replace(/:splat/g, "(?<splat>.*)").replace(/\//g, "\\/") + "$",
        "i",
    );
}

/**
 * A two-way map of redirects.
 */
export class RedirectsIndex {
    /**
     * @param {string[]} redirectsFiles
     * @returns {Promise<RedirectsIndex>}
     */
    static async build(...redirectsFiles) {
        const redirectsFileContent = await parseAllRedirects({
            redirectsFiles,
            configRedirects: [],
            minimal: true,
        });

        if (redirectsFileContent.errors.length) {
            console.error(redirectsFileContent.errors);
            throw new TypeError("Failed to parse redirects file.");
        }

        /**
         * @type {RedirectEntry[]}
         */
        // @ts-expect-error - dynamically generated.
        const redirectEntries = redirectsFileContent.redirects;

        return new RedirectsIndex(redirectEntries);
    }

    /**
     * @type {Map<RegExp, string>}
     */
    #fromMap = new Map();

    /**
     * @type {Map<RegExp, string>}
     */
    #destinationMap = new Map();

    /**
     * @type {Map<string, string>}
     */
    #aliasMap = new Map();

    /**
     *
     * @param {Iterable<RedirectEntry>} redirectEntries
     */
    constructor(redirectEntries) {
        for (const entry of redirectEntries) {
            const fromMatcher = pathnameToMatcher(entry.from);
            this.#fromMap.set(fromMatcher, entry.to);

            const destinationMatcher = destinationToMatcher(entry.to);
            this.#destinationMap.set(destinationMatcher, entry.from.replaceAll("*", ":splat"));

            if (!entry.from.includes("*")) {
                this.#aliasMap.set(entry.to, entry.from);
            }
        }
    }

    /**
     * @param {string} pathname
     * @returns {string}
     */
    rewriteFrom(pathname) {
        for (const [from, to] of this.#fromMap) {
            const match = from.exec(pathname);

            if (!match) continue;

            let result = to;

            if (!match.groups) return result;

            for (const [group, value] of Object.entries(match.groups)) {
                result = result.replace(`:${group}`, value);
            }

            return result;
        }

        return pathname;
    }

    /**
     * @param {string} pathname
     * @returns {string[]}
     */
    rewriteDestination(pathname) {
        const aliases = new Set();

        for (const [destinationMatcher, destination] of this.#destinationMap) {
            const alias = this.#aliasMap.get(pathname);

            if (alias) {
                aliases.add(alias);
            }

            const match = destinationMatcher.exec(pathname);

            if (!match) continue;

            let result = destination;

            if (!match.groups) {
                if (pathname === result) continue;

                aliases.add(result);
                continue;
            }

            for (const [group, value] of Object.entries(match.groups)) {
                result = result.replace(`:${group}`, value);
            }

            if (result === pathname) continue;

            aliases.add(result);
        }

        return Array.from(aliases);
    }
}
