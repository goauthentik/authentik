/**
 * @file Storybook manager configuration.
 */

import { extendStorybookTheme } from "./theme.js";

import { createUIThemeEffect } from "@goauthentik/web/common/theme.ts";

import { addons } from "storybook/manager-api";

createUIThemeEffect((nextUITheme) => {
    addons.setConfig({
        theme: extendStorybookTheme(nextUITheme),
        enableShortcuts: false,
    });
});
