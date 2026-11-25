/**
 * @file Storybook manager configuration.
 */

import { extendStorybookTheme } from "./theme.js";

import { applyThemeChoice, createUIThemeEffect } from "@goauthentik/web/common/theme.ts";

import { GLOBALS_UPDATED, SET_GLOBALS } from "storybook/internal/core-events";
import { addons } from "storybook/manager-api";

createUIThemeEffect((nextUITheme) => {
    addons.setConfig({
        theme: extendStorybookTheme(nextUITheme),
        enableShortcuts: false,
    });
});

// Load the theme so that it applies to all of storybook: the preview window, the border, and so on.
addons.register("authentik/theme", (api) => {
    /**
     * @param {{
     *     globals: { theme?: import("@goauthentik/web/common/theme.ts").CSSColorSchemeValue };
     * }} event
     */
    const syncThemeChoice = ({ globals }) => applyThemeChoice(globals.theme);

    api.on(SET_GLOBALS, syncThemeChoice);
    api.on(GLOBALS_UPDATED, syncThemeChoice);
});
