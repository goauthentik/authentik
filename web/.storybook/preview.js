/**
 * @file Storybook manager configuration.
 *
 * @import { Preview } from "@storybook/web-components";
 */

import "#styles/authentik/interface.global.css";
import "#styles/authentik/storybook.css";

import { ThemedDocsContainer } from "./DocsContainer.tsx";
import { extendStorybookTheme } from "./theme.js";

import {
    applyDocumentTheme,
    createUIThemeEffect,
    resolveUITheme,
} from "@goauthentik/web/common/theme.ts";

const base = resolveUITheme();
const theme = extendStorybookTheme(base);

applyDocumentTheme(base);

createUIThemeEffect(applyDocumentTheme);

/**
 * @satisfies {Preview}
 */
const preview = {
    tags: ["autodocs"],

    parameters: {
        docs: {
            theme,
            container: ThemedDocsContainer,
        },
        options: {
            storySort: {
                method: "alphabetical",
            },
        },
        actions: { argTypesRegex: "^on[A-Z].*" },

        controls: {
            matchers: {
                color: /(background|color)$/i,
                date: /Date$/,
            },
        },
    },
};

export default preview;
