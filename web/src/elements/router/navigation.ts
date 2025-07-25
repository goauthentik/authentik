import { ROUTE_SEPARATOR, RouteInterfaceName } from "#elements/router/constants";
import {
    decodeParameters,
    pluckRoute,
    PrimitiveRouteParameter,
    recordToSearchParams,
    RouteParameterRecord,
    RouterParameterInit,
} from "#elements/router/parsing";
import { readInterfaceRouteParam } from "#elements/router/utils";

/**
 * Create a route hash from a pathname and parameters.
 *
 * @param pathname The pathname of the route.
 * @param params The parameters to serialize.
 * @returns The formatted route hash, starting with `#`.
 */
export function paramURL(pathname: string, params?: RouterParameterInit): string {
    const routePrefix = "#" + pathname;

    if (!params) return routePrefix;

    const searchParams = recordToSearchParams(params);

    return [routePrefix, searchParams.toString()].join(ROUTE_SEPARATOR);
}

export function updateURLParams(params: RouteParameterRecord, replace = true): void {
    navigate((route) => ({
        ...route,
        params: {
            ...route.params,
            ...params,
        },
    }));
}

export function getURLParam<
    T extends PrimitiveRouteParameter | PrimitiveRouteParameter[] =
        | PrimitiveRouteParameter
        | PrimitiveRouteParameter[],
>(key: string) {
    const params = decodeParameters();

    return params[key] as T;
}

export interface RouteState {
    interfaceName: RouteInterfaceName;
    pathname: string;
    params: RouteParameterRecord;
    search?: RouteParameterRecord;
}

export type To = URL | string | Partial<RouteState> | ((currentRoute: RouteState) => RouteState);

export interface NavigateOptions {
    mode?: "push" | "replace" | "assign";
}

/**
 * Navigate to a route.
 *
 * @param {string} pathname The pathname of the route.
 * @param {RouteParameterRecord} params The parameters to serialize.
 */
export function navigate(to?: To, { mode = "replace" }: NavigateOptions = {}): void {
    if (!to) {
        console.warn("authentik/router: no destination provided, aborting navigation");
        return;
    }

    let next: URL;

    if (typeof to === "string" || to instanceof URL) {
        next = URL.canParse(to) ? new URL(to) : new URL(to, window.location.origin);
    } else if (typeof to === "function") {
        const nextRoute = to({
            interfaceName: readInterfaceRouteParam(),
            params: decodeParameters(),
            pathname: pluckRoute().pathname,
        });

        next = new URL(formatInterfaceRoute(nextRoute), window.location.origin);
    } else {
        next = new URL(
            formatInterfaceRoute({
                interfaceName: readInterfaceRouteParam(),
                ...to,
            }),
            window.location.origin,
        );
    }

    if (mode === "assign") {
        console.debug(`authentik/router: Assigning ${next.href}`);
        return window.location.assign(next);
    }

    if (next.href === window.location.href) {
        // Nothing to do.
        return;
    }

    console.debug(`authentik/router: (${mode}) navigating to ${next.href}`);

    if (mode === "replace") {
        return history.replaceState(undefined, "", next);
    }

    return history.pushState(undefined, "", next);
}

/**
 * Create a route to an interface by name, optionally with parameters.
 */
export function formatInterfaceRoute({
    interfaceName = readInterfaceRouteParam(),
    pathname = "/",
    params,
    search,
}: Partial<RouteState>): string {
    let pathBuilder = new URL(document.baseURI).pathname + `if/${interfaceName}/`;

    if (search) {
        pathBuilder += `?${recordToSearchParams(search).toString()}`;
    }

    return pathBuilder + paramURL(pathname, params);
}

export function toUserRoute(pathname: string, params?: RouteParameterRecord) {
    return formatInterfaceRoute({ interfaceName: "user", pathname, params });
}

export function toAdminRoute(pathname: string, params?: RouteParameterRecord) {
    return formatInterfaceRoute({ interfaceName: "admin", pathname, params });
}

export function toFlowRoute(pathname: string, params?: RouteParameterRecord) {
    return formatInterfaceRoute({ interfaceName: "flow", pathname, params });
}
