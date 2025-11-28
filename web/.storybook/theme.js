/**
 * @import { ResolvedUITheme } from "@goauthentik/web/common/theme.ts";
 * @import { ThemeVars } from "storybook/theming";
 */

import { themes as BaseThemes } from "storybook/theming";

/** @type {Partial<ThemeVars>} */
const brand = {
    brandTitle: "authentik Storybook",
    brandUrl: "https://goauthentik.io",
    brandImage: "https://goauthentik.io/img/icon_left_brand_colour.svg",
    brandTarget: "_self",
    barBg: "rgba(255,255,255,.05)",
    colorSecondary: "#fd4b2c",
    colorPrimary: "green",
};

/**
 * @type {Record<ResolvedUITheme, ThemeVars>}
 */
const themes = {
    light: {
        ...BaseThemes.light,
        appBg: "#fff",
        appContentBg: "hsl(9 88% 99%)",
        appPreviewBg: "hsl(9 88% 99%)",
    },
    dark: {
        ...BaseThemes.dark,
        appBg: "#1c1e21",
        appContentBg: "hsl(260 26% 5%)",
        appPreviewBg: "hsl(260 26% 5%)",
    },
};

/**
 * @param {ResolvedUITheme | ThemeVars} base
 * @returns {ThemeVars}
 */
export function extendStorybookTheme(base) {
    const theme = typeof base === "string" ? themes[base] : base || themes;

    return /** @type {ThemeVars} */ ({
        ...theme,
        ...brand,
    });
}
