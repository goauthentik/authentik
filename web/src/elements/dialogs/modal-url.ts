/**
 * @file URL bookkeeping for modals.
 *
 * A modal may change the page's search parameters while it is open — either its
 * slotted content (e.g. a paginated table) or its own deep-link state. When it
 * closes, those changes should not linger on the page URL.
 */

/**
 * Resolve the URL to write when a modal closes, or `null` when nothing should
 * change.
 *
 * Reverts to the URL captured when the modal opened — discarding any search
 * parameters its slotted content wrote while open — and additionally strips the
 * modal's own declared `ownedParams` (deep-link/trigger params), so opening a
 * modal from a URL never strands a parameter or re-opens on reload.
 *
 * Returns `null` when the modal navigated to a different path (it owns none of
 * the new URL) or when the resulting URL already matches the current one.
 *
 * @param urlOnOpen The page URL captured when the modal opened.
 * @param currentHref The current page URL.
 * @param ownedParams Search-param keys that represent the modal's own state.
 */
export function resolveModalCloseURL(
    urlOnOpen: string,
    currentHref: string,
    ownedParams: readonly string[],
): string | null {
    const restored = new URL(urlOnOpen);
    const current = new URL(currentHref);

    if (restored.pathname !== current.pathname) return null;

    for (const key of ownedParams) {
        restored.searchParams.delete(key);
    }

    return restored.href === current.href ? null : restored.href;
}
