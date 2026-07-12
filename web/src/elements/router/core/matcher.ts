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
 * @param pathname The pathname to match (already stripped of base + interface
 * prefix by the caller).
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
