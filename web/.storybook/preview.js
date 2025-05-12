/// <reference types="../types/css.js" />
/**
 * @file Storybook manager configuration.
 *
 * @import { Preview } from "@storybook/web-components";
 */
import { applyDocumentTheme } from "@goauthentik/web/common/theme.ts";

applyDocumentTheme();

/**
 * @satisfies {Preview}
 */
const preview = {
    parameters: {
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
