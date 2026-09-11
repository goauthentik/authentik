/**
 * @file Reader for the values the server injects into the interface documents.
 *
 * The server renders them as data — two `json_script` blocks and a handful of
 * `<meta>` tags — rather than as an executable `window.authentik` assignment,
 * so the interface pages can eventually be served under a strict CSP. See
 * `authentik/core/templates/base/header_js.html`.
 */

import { TargetLanguageTag } from "#common/ui/locale/definitions";
import { autoDetectLanguage } from "#common/ui/locale/utils";

import {
    Config,
    ConfigFromJSON,
    CurrentBrand,
    CurrentBrandFromJSON,
    FlowLayoutEnum,
} from "@goauthentik/api";

export interface GlobalAuthentik {
    locale: TargetLanguageTag;
    flow?: {
        layout: FlowLayoutEnum;
        title?: string;
        background?: string;
    };
    config: Config;
    brand: CurrentBrand;
    versionFamily: string;
    versionSubdomain: string;
    build: string;
    api: {
        base: string;
        relBase: string;
    };
}

/**
 * Read a server-injected `<meta>` value, if the document carries one.
 */
function readMeta(name: string): string | null {
    const element = document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`);

    return element?.content || null;
}

/**
 * Parse a server-injected `json_script` block, if the document carries one.
 *
 * A malformed block is treated as absent: the interface still boots on the
 * fallbacks below, which is strictly better than failing to render at all.
 */
function readJSONScript(id: string): unknown {
    const element = document.getElementById(id);

    if (!element?.textContent) return null;

    try {
        return JSON.parse(element.textContent);
    } catch (_error) {
        return null;
    }
}

function readServerContext(): GlobalAuthentik {
    const fallbackAPIBase = new URL(import.meta.env.AK_API_BASE_PATH || window.location.origin);

    const context: GlobalAuthentik = {
        locale: autoDetectLanguage(readMeta("ak-locale") ?? undefined),
        // `ConfigFromJSON`/`CurrentBrandFromJSON` pass a nullish value straight
        // through, so the empty shapes stand in when nothing was injected.
        config: ConfigFromJSON(readJSONScript("ak-config") ?? { capabilities: [] }),
        brand: CurrentBrandFromJSON(readJSONScript("ak-brand") ?? { ui_footer_links: [] }),
        versionFamily: readMeta("ak-version-family") ?? "",
        versionSubdomain: readMeta("ak-version-subdomain") ?? "",
        build: readMeta("ak-build") ?? "",
        api: {
            base: readMeta("ak-base-url") ?? fallbackAPIBase.toString(),
            relBase: readMeta("ak-base-url-rel") ?? fallbackAPIBase.pathname,
        },
    };

    const flowLayout = readMeta("ak-flow-layout");

    if (flowLayout) {
        context.flow = {
            layout: flowLayout as FlowLayoutEnum,
            title: readMeta("ak-flow-title") ?? undefined,
            background: readMeta("ak-flow-background") ?? undefined,
        };
    }

    return context;
}

let serverContext: GlobalAuthentik | null = null;

/**
 * Re-read the server context from the document, replacing the memoized value.
 *
 * Only useful to tests that swap the injected markup; the values are static for
 * the lifetime of a document.
 */
export function refreshServerContext(): GlobalAuthentik {
    serverContext = readServerContext();

    return serverContext;
}

/**
 * The values the server injected into this document.
 *
 * Memoized rather than evaluated at import, so this module stays importable
 * without a document — Node unit tests included.
 */
export function globalAK(): GlobalAuthentik {
    return (serverContext ??= readServerContext());
}

export function docLink(urlLike: string | URL, base = import.meta.env.AK_DOCS_URL): string {
    const url = new URL(urlLike, base);

    url.searchParams.append("utm_source", "authentik");

    return url.href;
}
