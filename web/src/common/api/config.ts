/**
 * @file Helpers for the `next` parameter used by redirects and flow steps.
 */

/**
 * Append a `next` parameter to a URL, preserving any existing query string.
 *
 * @param href The URL to extend, absolute or relative to the current origin.
 * @param next Where to return afterwards. Defaults to the current page.
 */
export function withNext(
    href: string,
    next: string = window.location.pathname + window.location.search,
): string {
    const url = new URL(href, window.location.origin);

    url.searchParams.set("next", next);

    return url.href;
}

/**
 * @deprecated Use {@linkcode withNext}, which keeps an existing query string intact.
 */
export function AndNext(url: string): string {
    return `?next=${encodeURIComponent(url)}`;
}
