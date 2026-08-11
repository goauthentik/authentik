/**
 * @file Search-parameter accessors for path-based routing.
 *
 * Drop-in replacements for the legacy hash-suffix `getURLParams`/`getURLParam`/
 * `updateURLParams` (`#elements/router/RouteMatch`), reading and writing real
 * `?` search parameters instead of the `#;{json}` suffix.
 */

import { navigate } from "#elements/router/core/navigation";
import {
    recordToSearchParams,
    type RouteParameterRecord,
    searchParamsToRecord,
} from "#elements/router/core/parameters";

/**
 * Read the current (or given) search string as a typed parameter record.
 */
export function getSearchParams(
    search: string = typeof window === "undefined" ? "" : window.location.search,
): RouteParameterRecord {
    return searchParamsToRecord(new URLSearchParams(search));
}

/**
 * Read a single search parameter, returning `fallback` when absent.
 */
export function getSearchParam<T>(key: string, fallback: T): T {
    const value = getSearchParams()[key];

    return (value === undefined ? fallback : value) as T;
}

/**
 * Merge `partial` into the current search parameters and write via
 * `history.replaceState`. Keys set to null/false/""/undefined are dropped.
 */
export function updateSearchParams(partial: RouteParameterRecord): void {
    const url = new URL(window.location.href);
    const merged = { ...searchParamsToRecord(url.searchParams), ...partial };

    url.search = recordToSearchParams(merged).toString();

    navigate(url, { mode: "replace" });
}
