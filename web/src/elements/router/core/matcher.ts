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
