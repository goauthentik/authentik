import { CurrentBrand, UiThemeEnum } from "@goauthentik/api";

// If the viewport is wider than MIN_WIDTH, the sidebar
// is shown besides the content, and not overlaid.
export const MIN_WIDTH = 1200;

export const DefaultBrand: CurrentBrand = {
    brandingLogo: "/static/dist/assets/icons/icon_left_brand.svg",
    brandingFavicon: "/static/dist/assets/icons/icon.png",
    brandingTitle: "authentik",
    brandingCustomCss: "",
    uiFooterLinks: [],
    uiTheme: UiThemeEnum.Automatic,
    matchedDomain: "",
    defaultLocale: "",
};
