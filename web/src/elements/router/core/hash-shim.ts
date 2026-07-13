/**
 * @file Legacy hash-route redirect shim (temporary).
 *
 * Translates legacy `#/path;<params>` URLs — both the JSON-blob encoding and
 * the `URLSearchParams` encoding — into path-based URLs, and applies the
 * translation via `history.replaceState` at boot.
 *
 * @remarks REMOVAL TARGET: delete this file two releases after the admin
 * interface ships on path routing (final step of the client-side routing
 * rollout).
 */

import { getRouterConfig } from "#elements/router/core/config";
import { formatInterfacePrefix } from "#elements/router/core/interfaces";
import {
    recordToSearchParams,
    type RouteParameterRecord,
    searchParamsToRecord,
} from "#elements/router/core/parameters";

/**
 * Separator between the legacy hash path and its serialized parameters.
 */
const LEGACY_PARAM_SEPARATOR = ";";

export interface HashRouteScope {
    base: string;
    interfaceName: string;
}

/**
 * Decode the serialized-parameter tail of a legacy hash route.
 *
 * Handles the JSON-blob encoding (`{"page":2}`, possibly percent-encoded) and
 * the `URLSearchParams` encoding (`a=1&b=true`).
 */
function decodeLegacyParams(serialized: string | undefined): RouteParameterRecord {
    if (!serialized) return {};

    const looksLikeJSON = serialized.startsWith("{") || serialized.startsWith("%7B");

    if (looksLikeJSON) {
        try {
            return JSON.parse(decodeURIComponent(serialized)) as RouteParameterRecord;
        } catch {
            return {};
        }
    }

    return searchParamsToRecord(new URLSearchParams(serialized));
}

/**
 * Translate a legacy hash route to a path-based URL.
 *
 * @param hash The `location.hash` value (including the leading `#`).
 * @param scope The deployment base and target interface.
 * @returns The translated path + search string, or `null` when `hash` is not a
 * legacy route (does not begin with `#/`).
 */
export function translateHashRoute(hash: string, scope: HashRouteScope): string | null {
    if (!hash.startsWith("#/")) return null;

    const withoutHash = hash.slice(1);
    const separatorIndex = withoutHash.indexOf(LEGACY_PARAM_SEPARATOR);

    const rawPath = separatorIndex === -1 ? withoutHash : withoutHash.slice(0, separatorIndex);
    const rawParams = separatorIndex === -1 ? undefined : withoutHash.slice(separatorIndex + 1);

    const segment = rawPath.replace(/^\/+/, "");
    const params = decodeLegacyParams(rawParams);
    const search = recordToSearchParams(params).toString();

    const prefix = formatInterfacePrefix(scope.base, scope.interfaceName);

    return `${prefix}${segment}${search ? `?${search}` : ""}`;
}

/**
 * Apply the hash-route redirect at boot, if the current URL is a legacy route.
 *
 * @param target The window whose location/history to read and rewrite.
 * @returns `true` when a redirect was applied.
 *
 * @remarks REMOVAL TARGET: delete with {@linkcode translateHashRoute}.
 */
export function applyHashRedirect(target: Window = window): boolean {
    const translated = translateHashRoute(target.location.hash, getRouterConfig());

    if (translated === null) return false;

    target.history.replaceState(null, "", translated);

    return true;
}
