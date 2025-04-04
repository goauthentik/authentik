import { ROUTE_SEPARATOR } from "@goauthentik/elements/router";
import type { Route, RouteParameterRecord } from "@goauthentik/elements/router/Route";

export interface RouteMatch<P extends RouteParameterRecord = RouteParameterRecord> {
    readonly route: Route<P>;
    readonly parameters: P;
    readonly pathname: string;
}

/**
 * Match a route against a pathname.
 */
export function matchRoute<P extends RouteParameterRecord>(
    pathname: string,
    routes: Route<P>[],
): RouteMatch<P> | null {
    if (!pathname) return null;

    for (const route of routes) {
        const match = route.pattern.exec({ pathname });

        if (!match) continue;

        console.debug(
            `authentik/router: matched route ${route.pattern} to ${pathname} with params`,
            match.pathname.groups,
        );
        return {
            route: route as Route<P>,
            parameters: match.pathname.groups as P,
            pathname,
        };
    }

    console.debug(`authentik/router: no route matched ${pathname}`);

    return null;
}

/**
 * Navigate to a route.
 *
 * @param {string} pathname The pathname of the route.
 * @param {RouteParameterRecord} params The parameters to serialize.
 */
export function navigate(pathname: string, params?: RouteParameterRecord): void {
    window.location.assign(formatRouteHash(pathname, params));
}

/**
 * Create a route hash from a pathname and parameters.
 *
 * @param {string} pathname The pathname of the route.
 * @param {RouteParameterRecord} params The parameters to serialize.
 * @returns {string} The formatted route hash, starting with `#`.
 * @see {@linkcode navigate} to navigate to a route.
 */
export function formatRouteHash(pathname: string, params?: RouteParameterRecord): string {
    const routePrefix = "#" + pathname;

    if (!params) return routePrefix;

    const searchParams = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
        if (typeof value === "boolean" && value) {
            searchParams.set(key, "true");
            continue;
        }

        if (typeof value === "undefined" || value === null) {
            continue;
        }

        if (Array.isArray(value)) {
            for (const item of value) {
                searchParams.append(key, item.toString());
            }

            continue;
        }

        searchParams.set(key, String(value));
    }

    return [routePrefix, searchParams.toString()].join(ROUTE_SEPARATOR);
}

/**
 * Create a route to an interface by name, optionally with parameters.
 */
export function formatInterfaceRoute(
    interfaceName: RouteInterfaceName,
    pathname?: string,
    params?: RouteParameterRecord,
): string {
    const prefix = `/if/${interfaceName}/`;

    if (!pathname) return prefix;

    return prefix + formatRouteHash(pathname, params);
}

export interface SerializedRoute {
    pathname: string;
    serializedParameters?: string;
}

export function pluckRoute(source: Pick<URL, "hash"> | string = window.location): SerializedRoute {
    source = typeof source === "string" ? new URL(source) : source;

    const [pathname, serializedParameters] = source.hash.slice(1).split(ROUTE_SEPARATOR, 2);

    return {
        pathname,
        serializedParameters,
    };
}

/**
 * Get a parameter from the current route.
 *
 * @template T - The type of the parameter.
 * @param {string} paramName - The name of the parameter to retrieve.
 * @param {T} fallback - The fallback value to return if the parameter is not found.
 */
export function getRouteParameter<T>(paramName: string, fallback: T): T {
    const params = getRouteParams();

    if (Object.hasOwn(params, paramName)) {
        return params[paramName] as T;
    }

    return fallback;
}

/**
 * Get the route parameters from the URL.
 *
 * @template T - The type of the route parameters.
 */
export function getRouteParams<T = RouteParameterRecord>(): T {
    const { serializedParameters } = pluckRoute();

    if (!serializedParameters) return {} as T;

    let searchParams: URLSearchParams;

    try {
        searchParams = new URLSearchParams(serializedParameters);
    } catch (_error) {
        console.warn("Failed to parse URL parameters", serializedParameters);
        return {} as T;
    }

    const decodedParameters: Record<string, unknown> = {};
    for (const [key, value] of searchParams.entries()) {
        if (value === "true" || value === "") {
            decodedParameters[key] = true;
            continue;
        }

        if (value === "false") {
            decodedParameters[key] = false;
            continue;
        }

        decodedParameters[key] = value;
    }

    return decodedParameters as T;
}

/**
 * Set the route parameters in the URL.
 *
 * @param nextParams - The JSON-serializable parameters to set in the URL.
 * @param replace - Whether to replace the current history entry or create a new one.
 */
export function setRouteParams(nextParams: RouteParameterRecord, replace = true): void {
    const { pathname } = pluckRoute();
    const nextHash = formatRouteHash(pathname, nextParams);

    if (replace) {
        history.replaceState(undefined, "", nextHash);
    } else {
        history.pushState(undefined, "", nextHash);
    }
}

/**
 * Patch the route parameters in the URL, retaining existing parameters not specified in the input.
 *
 * @param patchedParams - The parameters to patch in the URL.
 * @param replace - Whether to replace the current history entry or create a new one.
 *
 * @todo Most instances of this should be URL search params, not hash params.
 */
export function patchRouteParams(patchedParams: RouteParameterRecord, replace = true): void {
    const currentParams = getRouteParams();
    const nextParams = { ...currentParams, ...patchedParams };

    setRouteParams(nextParams, replace);
}

/**
 * Type guard to check if a given input is parsable as a URL.
 *
 * ```js
 * isURLInput("https://example.com") // true
 * isURLInput("invalid-url") // false
 * isURLInput(new URL("https://example.com")) // true
 * ```
 */
export function isURLInput(input: unknown): input is string | URL {
    if (typeof input !== "string" && !(input instanceof URL)) return false;

    if (!input) return false;

    return URL.canParse(input);
}

/**
 * The name identifier for the current interface.
 */
export type RouteInterfaceName = "user" | "admin" | "flow" | "unknown";

/**
 * Read the current interface route parameter from the URL.
 *
 * @param location - The location object to read the pathname from. Defaults to `window.location`.
 * * @returns The name of the current interface, or "unknown" if not found.
 */
export function readInterfaceRouteParam(
    location: Pick<URL, "pathname"> = window.location,
): RouteInterfaceName {
    const [, currentInterface = "unknown"] = location.pathname.match(/.+if\/(\w+)\//) || [];

    return currentInterface.toLowerCase() as RouteInterfaceName;
}

/**
 * Predicate to determine if the current route is for the admin interface.
 */
export function isAdminRoute(location: Pick<URL, "pathname"> = window.location): boolean {
    return readInterfaceRouteParam(location) === "admin";
}

/**
 * Predicate to determine if the current route is for the user interface.
 */
export function isUserRoute(location: Pick<URL, "pathname"> = window.location): boolean {
    return readInterfaceRouteParam(location) === "user";
}
