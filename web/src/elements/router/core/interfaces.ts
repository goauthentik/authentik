/**
 * @file Cross-interface href builders.
 *   The only sanctioned channel for referencing another interface: these return
 *   full, base-path-aware URL strings for use with plain `<a href>` /
 *   `location.assign`. Crossing interfaces is a real page load (a different
 *   bundle). Fixes the hardcoded `/if/user/` literals that break under a
 *   non-root `web.path`.
 */

import { getRouterConfig } from "#elements/router/core/config";
import { recordToSearchParams, type RouterParameterInit } from "#elements/router/core/parameters";
import { ensureTrailingSlash, stripLeadingSlash, stripPrefix } from "#elements/router/core/paths";

/**
 * Build the pathname prefix owned by an interface, e.g. `/auth/if/admin/`.
 *
 * The single source of truth for prefix construction — the href builders,
 * click interceptor, and hash shim must all agree byte-for-byte.
 */
export function formatInterfacePrefix(base: string, interfaceName: string): string {
    return `${ensureTrailingSlash(base)}if/${interfaceName}/`;
}

function buildSearch(params?: RouterParameterInit): string {
    if (!params) return "";

    const search = recordToSearchParams(params).toString();

    return search ? `?${search}` : "";
}

/**
 * The current pathname relative to the interface that created the router.
 *
 * This is useful for interface-agnostic components such as the sidebar
 * that need to know which routes are active without owning an outlet of their own.
 */
export function currentInterfacePath(pathname: string = window.location.pathname): string {
    const { base, interfaceName } = getRouterConfig();

    return stripPrefix(pathname, formatInterfacePrefix(base, interfaceName));
}

/**
 * Build a full, base-path-aware URL for the given interface.
 *
 * @param interfaceName The target interface segment, e.g. `admin`.
 * @param path The path within the interface, with or without a leading slash.
 * @param params Optional search parameters.
 */
export function formatInterfaceURL(
    interfaceName: string,
    path = "",
    params?: RouterParameterInit,
): string {
    const { base } = getRouterConfig();
    const prefix = formatInterfacePrefix(base, interfaceName);

    return `${prefix}${stripLeadingSlash(path)}${buildSearch(params)}`;
}

/**
 * Build a URL into the admin interface.
 */
export function toAdminInterface(path?: string, params?: RouterParameterInit): string {
    return formatInterfaceURL("admin", path, params);
}

/**
 * Build a URL into the user interface.
 */
export function toUserInterface(path?: string, params?: RouterParameterInit): string {
    return formatInterfaceURL("user", path, params);
}

/**
 * Build a URL into the currently-configured interface.
 *
 * For interface-agnostic shared components (sidebar, navbar) that link within
 * whichever interface booted the router, rather than a fixed target.
 */
export function toCurrentInterface(path?: string, params?: RouterParameterInit): string {
    return formatInterfaceURL(getRouterConfig().interfaceName, path, params);
}

/**
 * Build a URL into the flow interface for a given flow slug.
 *
 * The flow interface keeps its server-driven, trailing-slashed URL space
 * (`/if/flow/<slug>/`).
 */
export function toFlowInterface(slug: string, params?: RouterParameterInit): string {
    return formatInterfaceURL("flow", ensureTrailingSlash(slug), params);
}
