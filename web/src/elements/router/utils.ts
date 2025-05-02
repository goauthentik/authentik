/**
 * @file Utilities for working with the client-side page router.
 */

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
