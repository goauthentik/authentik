import { TargetLocale } from "#common/ui/locale/definitions";
import { autoDetectLanguage } from "#common/ui/locale/utils";

import {
    Config,
    ConfigFromJSON,
    CurrentBrand,
    CurrentBrandFromJSON,
    FlowLayoutEnum,
} from "@goauthentik/api";

const convertedSymbol = Symbol("ak-converted");

export interface GlobalAuthentik {
    [convertedSymbol]?: boolean;
    locale: TargetLocale;
    flow?: {
        layout: FlowLayoutEnum;
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

export interface AuthentikWindow {
    authentik: GlobalAuthentik;
}

export function globalAK(): GlobalAuthentik {
    const ak = (window as unknown as AuthentikWindow).authentik;

    if (!ak) {
        const apiBase = new URL(import.meta.env.AK_API_BASE_PATH || window.location.origin);

        return {
            locale: autoDetectLanguage(),
            config: ConfigFromJSON({
                capabilities: [],
            }),
            brand: CurrentBrandFromJSON({
                ui_footer_links: [],
            }),
            versionFamily: "",
            versionSubdomain: "",
            build: "",
            api: {
                base: apiBase.toString(),
                relBase: apiBase.pathname,
            },
        };
    }

    if (!ak[convertedSymbol]) {
        ak.locale = autoDetectLanguage(ak.locale);
        ak.brand = CurrentBrandFromJSON(ak.brand);
        ak.config = ConfigFromJSON(ak.config);

        ak[convertedSymbol] = true;
    }

    return ak;
}

export function docLink(urlLike: string | URL, base = import.meta.env.AK_DOCS_URL): string {
    const url = new URL(urlLike, base);

    url.searchParams.append("utm_source", "authentik");

    return url.href;
}
