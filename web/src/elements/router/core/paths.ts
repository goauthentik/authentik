/**
 * @file Pathname normalization shared across the router core.
 *   Joining and splitting pathnames is the one operation every part of the router
 *   does — the outlet, the href builders, the hash shim, the span namer — and it
 *   is exactly the kind of thing that drifts when each one spells it out inline.
 *   They all go through here so a prefix with or without a trailing slash, and a
 *   path with or without a leading one, can never produce `//` or a missing `/`.
 */

/**
 * Drop any leading slashes: `/settings` → `settings`, `//x` → `x`.
 */
export function stripLeadingSlash(value: string): string {
    return value.replace(/^\/+/, "");
}

/**
 * Drop any trailing slashes: `/if/user/` → `/if/user`, `/` → `""`.
 */
export function stripTrailingSlash(value: string): string {
    return value.replace(/\/+$/, "");
}

/**
 * Ensure exactly one trailing slash: `/auth` → `/auth/`, `/auth/` unchanged.
 */
export function ensureTrailingSlash(value: string): string {
    return value.endsWith("/") ? value : `${value}/`;
}

/**
 * Join a path onto a prefix with exactly one separator, regardless of whether
 * the prefix ends in a slash or the path begins with one.
 */
export function joinPath(prefix: string, path: string): string {
    return `${stripTrailingSlash(prefix)}/${stripLeadingSlash(path)}`;
}

/**
 * Strip `prefix` from `pathname`, preserving the leading slash the matcher
 * requires: `/if/user/settings` → `/settings`, `/if/user/` → `/`.
 *
 * Matching is segment-aware, so a prefix without a trailing slash (a nested
 * outlet's base, e.g. `…/users/22`) never captures a sibling that merely shares
 * its text (`…/users/220`). A pathname outside the prefix is returned unchanged,
 * so the outlet can let it fall through to its 404 branch.
 */
export function stripPrefix(pathname: string, prefix: string): string {
    const base = stripTrailingSlash(prefix);

    if (pathname === base) return "/";

    if (pathname.startsWith(`${base}/`)) {
        return `/${stripLeadingSlash(pathname.slice(base.length + 1))}`;
    }

    return pathname;
}
