/**
 * @import { Preview } from "@storybook/web-components";
 * @file Storybook manager configuration.
 */

import "@goauthentik/fonts/faces.css";
import "@goauthentik/fonts/icons.css";
import "#styles/if/authenticated/index.global.css";
import "#styles/if/shared/static.global.css";
import "./preview.css";
import { ThemedDocsContainer } from "./DocsContainer.tsx";
import { extendStorybookTheme } from "./theme.js";

import {
    applyDocumentTheme,
    applyThemeChoice,
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

    globalTypes: {
        theme: {
            description: "authentik color scheme",
            toolbar: {
                title: "Theme",
                icon: "mirror",
                items: [
                    { value: "auto", title: "System", icon: "mirror" },
                    { value: "light", title: "Light", icon: "sun" },
                    { value: "dark", title: "Dark", icon: "moon" },
                ],
                dynamicTitle: true,
            },
        },
    },

    initialGlobals: {
        theme: "auto",
    },

    decorators: [
        // Ensure the current theme choice is always active before rendering a story.
        (story, { globals }) => {
            applyThemeChoice(globals.theme);

            return story();
        },
    ],

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
