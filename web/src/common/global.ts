/**
 * @file Reader for the values the server injects into the interface documents.
 *   The server renders them as data — two `json_script` blocks and a handful of `<meta>` tags.
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
import { ServerContextMeta } from "@goauthentik/core/document";
import { readJSONScript, readMeta } from "@goauthentik/core/document/browser";

export interface FlowMeta {
    layout: FlowLayoutEnum;
    title?: string;
    background?: string;
}

export interface GlobalAuthentik {
    locale: TargetLanguageTag;
    flow?: FlowMeta;
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
 * Read the current brand from the document.
 */
export function readCurrentBrand(): CurrentBrand {
    return CurrentBrandFromJSON(readJSONScript(ServerContextMeta.Brand) ?? { ui_footer_links: [] });
}

/**
 * Read the configuration from the document.
 */
export function readConfig(): Config {
    return ConfigFromJSON(readJSONScript(ServerContextMeta.Config) ?? { capabilities: [] });
}

function readServerContext(): GlobalAuthentik {
    const fallbackAPIBase = new URL(import.meta.env.AK_API_BASE_PATH || window.location.origin);

    const context: GlobalAuthentik = {
        locale: autoDetectLanguage(readMeta(ServerContextMeta.Locale)),
        // `ConfigFromJSON`/`CurrentBrandFromJSON` pass a nullish value straight
        // through, so the empty shapes stand in when nothing was injected.
        config: readConfig(),
        brand: readCurrentBrand(),
        versionFamily: readMeta(ServerContextMeta.VersionFamily) ?? "",
        versionSubdomain: readMeta(ServerContextMeta.VersionSubdomain) ?? "",
        build: readMeta(ServerContextMeta.Build) ?? "",
        api: {
            base: readMeta(ServerContextMeta.BaseURL) ?? fallbackAPIBase.toString(),
            relBase: readMeta(ServerContextMeta.BaseURLRel) ?? fallbackAPIBase.pathname,
        },
    };

    const flowLayout = readMeta(ServerContextMeta.FlowLayout);

    if (flowLayout) {
        context.flow = {
            layout: flowLayout as FlowLayoutEnum,
            title: readMeta(ServerContextMeta.FlowTitle) ?? undefined,
            background: readMeta(ServerContextMeta.FlowBackground) ?? undefined,
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
