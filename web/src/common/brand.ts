/**
 * Utilities for injecting and managing the authentik brand.
 */

import { refreshServerContext } from "#common/global";

import { CurrentBrand, CurrentBrandToJSON, FooterLinkToJSON, UiThemeEnum } from "@goauthentik/api";
import { ServerContextMeta } from "@goauthentik/core/document";
import { createJSONScriptElement, injectOrSwap } from "@goauthentik/core/document/browser";

export type InjectableCurrentBrand = Partial<CurrentBrand>;

/**
 * The brand an unconfigured instance would render.
 */
export const DefaultCurrentBrand: CurrentBrand = {
    matchedDomain: "",
    brandingTitle: "authentik",
    brandingLogo: "",
    brandingLogoThemedUrls: null,
    brandingFavicon: "",
    brandingFaviconThemedUrls: null,
    brandingCustomCss: "",
    brandingMapTiles: "",
    uiFooterLinks: [],
    uiTheme: UiThemeEnum.Automatic,
    defaultLocale: "",
    flags: {
        flowsContinuousLogin: false,
    },
};

/**
 * Inject the brand the server would render into the document.
 */
export function injectBrand(overrides: InjectableCurrentBrand = {}): void {
    const brand: CurrentBrand = { ...DefaultCurrentBrand, ...overrides };

    // The generated serializer skips read-only fields, which the server still renders.
    const data = {
        ...CurrentBrandToJSON(brand),
        ui_footer_links: brand.uiFooterLinks.map(FooterLinkToJSON),
        ui_theme: brand.uiTheme,
        default_locale: brand.defaultLocale,
    };

    injectOrSwap(createJSONScriptElement(data, ServerContextMeta.Brand));

    refreshServerContext();
}
