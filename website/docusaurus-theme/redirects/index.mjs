/**
 * @file Docusaurus redirects utils.
 */

import escapeStringRegexp from "escape-string-regexp";

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
    const matcher = escapeStringRegexp(pathname)
        .replace(/\\\*/g, "(?<splat>.*)")
        .replace(/\//g, "\\/");

    return new RegExp("^" + matcher + (pathname.includes("*") ? "" : "$"), "i");
}

/**
 * @param {string} pathname
 * @returns {string}
 */
function normalizeAliasPathname(pathname) {
    return pathname.replace(/\/+$/, "") || "/";
}

/**
 * Given a destination, return a RegExp that matches the destination.
 *
 * This is used to match the inverse of a pathname matcher.
 * @param {string} destination
 * @returns {RegExp}
 */
export function destinationToMatcher(destination) {
    const safeDestination = escapeStringRegexp(destination)
        .replace(/:splat/g, "(?<splat>.*)")
        .replace(/\//g, "\\/");
    return new RegExp("^" + safeDestination + "$", "i");
}

/**
 * A two-way map of route rewrites.
 */
export class RewriteIndex {
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
     * Find the final destination for the given pathname, following all redirects.
     *
     * @param {string} pathname
     * @returns {string}
     */
    finalDestination(pathname) {
        if (!pathname) return pathname;

        let destination = this.findNextDestination(pathname);

        while (true) {
            const next = this.findNextDestination(destination);

            if (next === destination) {
                break;
            }

            destination = next;
        }

        return destination ?? pathname;
    }

    /**
     * Find the next destination for the given pathname.
     *
     * @param {string} pathname
     * @returns {string}
     */
    findNextDestination(pathname) {
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
    findAliases(pathname) {
        /**
         * @type {Map<string, string>}
         */
        const aliases = new Map();
        const addAlias = (alias) => {
            if (normalizeAliasPathname(alias) === normalizeAliasPathname(pathname)) return;

            aliases.set(normalizeAliasPathname(alias), alias);
        };

        for (const [destinationMatcher, destination] of this.#destinationMap) {
            const alias = this.#aliasMap.get(pathname);

            if (alias) {
                addAlias(alias);
            }

            const match = destinationMatcher.exec(pathname);

            if (!match) continue;

            let result = destination;

            if (!match.groups) {
                addAlias(result);
                continue;
            }

            for (const [group, value] of Object.entries(match.groups)) {
                result = result.replace(`:${group}`, value);
            }

            addAlias(result);
        }

        return Array.from(aliases.values());
    }
}
