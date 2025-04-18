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
