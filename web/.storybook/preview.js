/// <reference types="../types/css.js" />
/**
 * @file Storybook manager configuration.
 *
 * @import { Preview } from "@storybook/web-components";
 */
import { UiThemeEnum } from "@goauthentik/api/dist/models/UiThemeEnum";
import { setAdoptedStyleSheets } from "@goauthentik/web/common/stylesheets.ts";
import { $AKBase, $AKBaseDark, $PFBase, resolveUITheme } from "@goauthentik/web/common/theme.ts";

setAdoptedStyleSheets(document, (currentStyleSheets) => {
    const uiTheme = resolveUITheme();

    return [
        // ---
        ...currentStyleSheets,
        $PFBase,
        $AKBase,
        ...(uiTheme === UiThemeEnum.Dark ? [$AKBaseDark] : []),
    ];
});

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
