import {
    CSRFMiddleware,
    EventMiddleware,
    LoggingMiddleware,
} from "@goauthentik/common/api/middleware";
import { EVENT_LOCALE_REQUEST, VERSION } from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";

import { Config, Configuration, CoreApi, CurrentBrand, RootApi } from "@goauthentik/api";

let globalConfigPromise: Promise<Config> | undefined = Promise.resolve(globalAK().config);
export function config(): Promise<Config> {
    if (!globalConfigPromise) {
        globalConfigPromise = new RootApi(DEFAULT_CONFIG).rootConfigRetrieve();
    }
    return globalConfigPromise;
}

export function brandSetFavicon(brand: CurrentBrand) {
    /**
     *  <link rel="icon" href="/static/dist/assets/icons/icon.png">
     *  <link rel="shortcut icon" href="/static/dist/assets/icons/icon.png">
     */
    const rels = ["icon", "shortcut icon"];
    rels.forEach((rel) => {
        let relIcon = document.head.querySelector<HTMLLinkElement>(`link[rel='${rel}']`);
        if (!relIcon) {
            relIcon = document.createElement("link");
            relIcon.rel = rel;
            document.getElementsByTagName("head")[0].appendChild(relIcon);
        }
        relIcon.href = brand.brandingFavicon;
    });
}

export function brandSetLocale(brand: CurrentBrand) {
    if (brand.defaultLocale === "") {
        return;
    }
    console.debug("authentik/locale: setting locale from brand default");
    window.dispatchEvent(
        new CustomEvent(EVENT_LOCALE_REQUEST, {
            composed: true,
            bubbles: true,
            detail: { locale: brand.defaultLocale },
        }),
    );
}

let globalBrandPromise: Promise<CurrentBrand> | undefined = Promise.resolve(globalAK().brand);
export function brand(): Promise<CurrentBrand> {
    if (!globalBrandPromise) {
        globalBrandPromise = new CoreApi(DEFAULT_CONFIG)
            .coreBrandsCurrentRetrieve()
            .then((brand) => {
                brandSetFavicon(brand);
                brandSetLocale(brand);
                return brand;
            });
    }
    return globalBrandPromise;
}

export function getMetaContent(key: string): string {
    const metaEl = document.querySelector<HTMLMetaElement>(`meta[name=${key}]`);
    if (!metaEl) return "";
    return metaEl.content;
}

export const DEFAULT_CONFIG = new Configuration({
    basePath: `${globalAK().api.base}api/v3`,
    headers: {
        "sentry-trace": getMetaContent("sentry-trace"),
    },
    middleware: [
        new CSRFMiddleware(),
        new EventMiddleware(),
        new LoggingMiddleware(globalAK().brand),
    ],
});

console.debug(`authentik(early): version ${VERSION}, apiBase ${DEFAULT_CONFIG.basePath}`);
