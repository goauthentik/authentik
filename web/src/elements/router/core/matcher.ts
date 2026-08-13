/**
 * @file Pure route matcher.
 *
 * First-match-wins linear scan over pre-compiled `URLPattern`s. No globals,
 * no side effects. Depends only on the structural shape of a route (a compiled
 * `pattern`), so it never imports `Route`.
 */

/**
 * The minimal shape the matcher needs from a route: a compiled pattern.
 */
export interface RoutePatternLike {
    readonly pattern: URLPattern;
}

export interface RouteMatch<R extends RoutePatternLike> {
    readonly route: R;
    readonly parameters: Record<string, string | undefined>;
    readonly pathname: string;
}

/**
 * Match a pathname against a route table, first-match-wins.
 *
 * @param pathname The interface-relative pathname, beginning with `/`.
 * The interface root is `/`. Callers stripping the interface prefix from
 * `location.pathname` must keep (or restore) the leading slash:
 * `/if/admin/users/42` → `/users/42`, `/if/admin/` → `/`.
 * @param routes The route table, scanned in order.
 * @returns The first match, or `null` when nothing matches.
 */
export function matchRoute<R extends RoutePatternLike>(
    pathname: string,
    routes: readonly R[],
): RouteMatch<R> | null {
    if (!pathname) return null;

    for (const route of routes) {
        const match = route.pattern.exec({ pathname });

        if (!match) continue;

        return {
            route,
            parameters: match.pathname.groups,
            pathname,
        };
    }

    return null;
}

/**
 * `URLPattern` names unnamed groups — `*` and `(.*)` — with sequential integer
 * keys. A route that matches a subtree (`/users/:id{/*}?`) captures the tail
 * this way, and that tail is sub-navigation the *mounted* view owns (its tabs),
 * not the identity of the mount. Named groups (`:id`) identify the mount.
 */
const WILDCARD_GROUP_KEY = /^\d+$/;

function identifyingKeys(parameters: Record<string, string | undefined>): string[] {
    return Object.keys(parameters).filter((key) => !WILDCARD_GROUP_KEY.test(key));
}

/**
 * Whether two matches resolve to the same mounted view: the same route with the
 * same *identifying* (named) path parameters. {@linkcode matchRoute} returns a
 * fresh object every call, so a search-only navigation (a table filter) or a
 * wildcard-tail change (a tab, in a subtree route) yields an equal-but-new match
 * — comparing structurally lets the outlet skip re-resolving it, which would
 * otherwise tear down and reload an already-mounted view.
 *
 * The wildcard tail is deliberately excluded: a subtree route stays mounted
 * while its tabs move through the tail, and the nested outlet inside it handles
 * the tail. A change to a named parameter (a different `:id`) still remounts.
 */
export function sameRouteMatch<R extends RoutePatternLike>(
    a: RouteMatch<R> | null,
    b: RouteMatch<R> | null,
): boolean {
    if (a === b) return true;
    if (a === null || b === null) return false;
    if (a.route !== b.route) return false;

    const aKeys = identifyingKeys(a.parameters);
    const bKeys = identifyingKeys(b.parameters);

    if (aKeys.length !== bKeys.length) return false;

    return aKeys.every((key) => a.parameters[key] === b.parameters[key]);
}
