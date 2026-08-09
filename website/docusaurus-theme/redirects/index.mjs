/**
 * @file Docusaurus redirects utils.
 *
 * Shared between build-time site configs (Node.js) and the client-side
 * router (see `theme/NotFound`), so this module must remain browser-safe.
 */

import escapeStringRegexp from "escape-string-regexp";

/**
 * Name of the Docusaurus plugin exposing redirect entries as global data.
 */
export const REDIRECTS_PLUGIN_NAME = "ak-redirects-plugin";

/**
 * @typedef {Object} RedirectEntry
 *
 * @property {string} from
 * @property {string} to
 * @property {boolean} force
 */

const SPLAT_GROUP_PATTERN = "(?<splat>.*)";

/**
 * Given a pathname, return a RegExp that matches the pathname.
 *
 * A `*` splat captures the remainder of the pathname; without one, the
 * matcher only matches the pathname exactly.
 *
 * @param {string} pathname
 * @returns {RegExp}
 */
export function pathnameToMatcher(pathname) {
    const matcher = pathname
        .split("*")
        .map((part) => escapeStringRegexp(part))
        .join(SPLAT_GROUP_PATTERN);

    return new RegExp("^" + matcher + (pathname.includes("*") ? "" : "$"), "i");
}

/**
 * Given a destination, return a RegExp that matches the destination.
 *
 * This is used to match the inverse of a pathname matcher.
 *
 * @param {string} destination
 * @returns {RegExp}
 */
export function destinationToMatcher(destination) {
    const matcher = destination
        .split(":splat")
        .map((part) => escapeStringRegexp(part))
        .join(SPLAT_GROUP_PATTERN);

    return new RegExp("^" + matcher + "$", "i");
}

/**
 * Replace `:name` placeholders (e.g. `:splat`) with their matched values.
 *
 * @param {string} template
 * @param {Record<string, string>} groups
 * @returns {string}
 */
function expandTemplate(template, groups) {
    let result = template;

    for (const [name, value] of Object.entries(groups)) {
        result = result.replace(`:${name}`, value);
    }

    return result;
}

/**
 * Trim trailing slashes for alias comparison.
 *
 * Scans the string instead of using a `/\/+$/` regex, which needs
 * polynomial backtracking time on pathnames made of many slashes.
 *
 * @param {string} pathname
 * @returns {string}
 */
function normalizeAliasPathname(pathname) {
    let end = pathname.length;

    while (end > 0 && pathname[end - 1] === "/") {
        end -= 1;
    }

    return pathname.slice(0, end) || "/";
}

/**
 * A redirect entry compiled for matching in both directions.
 *
 * @typedef {Object} RewriteRule
 *
 * @property {RegExp} fromMatcher matches pathnames against the entry's source
 * @property {string} toTemplate the destination, with `:splat` placeholders
 * @property {RegExp} destinationMatcher matches pathnames against the entry's destination
 * @property {string} fromTemplate the source, with `*` rewritten to `:splat`
 */

/**
 * A two-way map of route rewrites.
 */
export class RewriteIndex {
    /**
     * @type {RewriteRule[]}
     */
    #rules = [];

    /**
     * Exact destination → source for entries without a splat.
     *
     * @type {Map<string, string>}
     */
    #aliasByDestination = new Map();

    /**
     * @param {Iterable<RedirectEntry>} redirectEntries
     */
    constructor(redirectEntries) {
        for (const entry of redirectEntries) {
            this.#rules.push({
                fromMatcher: pathnameToMatcher(entry.from),
                toTemplate: entry.to,
                destinationMatcher: destinationToMatcher(entry.to),
                fromTemplate: entry.from.replaceAll("*", ":splat"),
            });

            if (!entry.from.includes("*")) {
                this.#aliasByDestination.set(entry.to, entry.from);
            }
        }
    }

    /**
     * Find the next destination for the given pathname, i.e. the first
     * matching rule's destination. Returns the pathname unchanged when no
     * rule matches.
     *
     * @param {string} pathname
     * @returns {string}
     */
    findNextDestination(pathname) {
        for (const { fromMatcher, toTemplate } of this.#rules) {
            const match = fromMatcher.exec(pathname);

            if (!match) continue;

            return match.groups ? expandTemplate(toTemplate, match.groups) : toTemplate;
        }

        return pathname;
    }

    /**
     * Find the final destination for the given pathname, following redirects
     * until they settle. Cyclic redirect chains stop at the first repeated
     * pathname.
     *
     * @param {string} pathname
     * @returns {string}
     */
    finalDestination(pathname) {
        if (!pathname) return pathname;

        const visited = new Set([pathname]);
        let destination = pathname;

        for (;;) {
            const next = this.findNextDestination(destination);

            if (next === destination || visited.has(next)) break;

            visited.add(next);
            destination = next;
        }

        return destination;
    }

    /**
     * Find every source pathname redirecting to the given pathname.
     *
     * Aliases are deduplicated ignoring trailing slashes, and the pathname
     * itself is never included.
     *
     * @param {string} pathname
     * @returns {string[]}
     */
    findAliases(pathname) {
        const normalizedPathname = normalizeAliasPathname(pathname);

        /**
         * @type {Map<string, string>} normalized alias → alias
         */
        const aliases = new Map();

        /**
         * @param {string} alias
         */
        const addAlias = (alias) => {
            const normalized = normalizeAliasPathname(alias);

            if (normalized === normalizedPathname) return;

            aliases.set(normalized, alias);
        };

        const exactAlias = this.#aliasByDestination.get(pathname);

        if (exactAlias) {
            addAlias(exactAlias);
        }

        for (const { destinationMatcher, fromTemplate } of this.#rules) {
            const match = destinationMatcher.exec(pathname);

            if (!match) continue;

            addAlias(match.groups ? expandTemplate(fromTemplate, match.groups) : fromTemplate);
        }

        return Array.from(aliases.values());
    }
}
