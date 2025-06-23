/**
 * @file Utilities for working with the client-side page router.
 */
import { kebabCase } from "change-case";

/**
 * The name identifier for the current interface.
 *
 * @category Routing
 */
export type RouteInterfaceName = "user" | "admin" | "flow" | "unknown";

/**
 * Read the current interface route parameter from the URL.
 *
 * @param location - The location object to read the pathname from. Defaults to `window.location`.
 * @returns The name of the current interface, or "unknown" if not found.
 *
 * @category Routing
 */
export function readInterfaceRouteParam(
    location: Pick<URL, "pathname"> = window.location,
): RouteInterfaceName {
    const [, currentInterface = "unknown"] = location.pathname.match(/.+if\/(\w+)\//) || [];

    return currentInterface.toLowerCase() as RouteInterfaceName;
}

/**
 * Predicate to determine if the current route is for the admin interface.
 *
 * @category Routing
 */
export function isAdminRoute(location: Pick<URL, "pathname"> = window.location): boolean {
    return readInterfaceRouteParam(location) === "admin";
}

/**
 * Predicate to determine if the current route is for the user interface.
 *
 * @category Routing
 */
export function isUserRoute(location: Pick<URL, "pathname"> = window.location): boolean {
    return readInterfaceRouteParam(location) === "user";
}

/**
 * Format a string to a URL-safe route slug.
 *
 * The input is converted to lowercase and non-alphanumeric characters are
 * replaced with a hyphen. Trailing whitespace and hyphens are removed.
 *
 * @param input - The input string to format.
 *
 * @category Routing
 *
 * ```ts
 * formatSlug("My Application"); // "my-application"
 * formatSlug(" 123ABC "); // "123-ABC"
 * formatSlug("-action-Name-"); // "action-name"
 * ```
 */
export function formatSlug(input: string): string {
    return kebabCase(input);
}

/**
 * Predicate to determine if the input is a valid route slug.
 *
 * @param input - The input string to check.
 */
export function isSlug(input: string): boolean {
    return kebabCase(input) === input;
}
