/**
 * @file Storybook manager configuration.
 *
 * @import { ThemeVarsPartial } from "storybook/internal/theming";
 */
import { createUIThemeEffect, resolveUITheme } from "@goauthentik/web/common/theme.ts";
import { addons } from "@storybook/manager-api";
import { create } from "@storybook/theming/create";

/**
 * @satisfies {Partial<ThemeVarsPartial>}
 */
const baseTheme = {
    brandTitle: "authentik Storybook",
    brandUrl: "https://goauthentik.io",
    brandImage: "https://goauthentik.io/img/icon_left_brand_colour.svg",
    brandTarget: "_self",
};

const uiTheme = resolveUITheme();

addons.setConfig({
    theme: create({
        ...baseTheme,
        base: uiTheme,
    }),
    enableShortcuts: false,
});

createUIThemeEffect((nextUITheme) => {
    addons.setConfig({
        theme: create({
            ...baseTheme,
            base: nextUITheme,
        }),
        enableShortcuts: false,
    });
});
