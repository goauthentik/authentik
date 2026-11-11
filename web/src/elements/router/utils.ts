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

export type URLContext = Pick<URL, "pathname">;

/**
 * Read the current interface route parameter from the URL.
 *
 * @category Routing
 * @param context The URL-like object to read the pathname from. Defaults to `window.location`.
 *
 * @returns The name of the current interface, or "unknown" if not found.
 */
export function readInterfaceRouteParam(context: URLContext = window.location): RouteInterfaceName {
    const [, currentInterface = "unknown"] = context.pathname.match(/.+if\/(\w+)\//) || [];

    return currentInterface.toLowerCase() as RouteInterfaceName;
}

/**
 * Predicate to determine if the current route is for the admin interface.
 *
 * @category Routing
 */
export function isAdminRoute(context: URLContext = window.location): boolean {
    return readInterfaceRouteParam(context) === "admin";
}

/**
 * Predicate to determine if the current route is for the user interface.
 *
 * @category Routing
 */
export function isUserRoute(context: URLContext = window.location): boolean {
    return readInterfaceRouteParam(context) === "user";
}

/**
 * Format a string to a URL-safe route slug.
 *
 * The input is converted to lowercase and non-alphanumeric characters are
 * replaced with a hyphen. Trailing whitespace and hyphens are removed.
 *
 * @category Routing
 *
 *   ```ts
 *   formatSlug("My Application"); // "my-application"
 *   formatSlug(" 123ABC "); // "123-ABC"
 *   formatSlug("-action-Name-"); // "action-name"
 *   ```
 * @param input The input string to format.
 */
export function formatSlug(input: string): string {
    return kebabCase(input);
}

/**
 * Predicate to determine if the input is a valid route slug.
 *
 * @param input The input string to check.
 */
export function isSlug(input: string): boolean {
    return kebabCase(input) === input;
}
