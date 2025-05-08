import { UiThemeEnum } from "@goauthentik/api/dist/models/UiThemeEnum";
import { setAdoptedStyleSheets } from "@goauthentik/web/common/stylesheets.js";
import { $AKBase, $AKBaseDark, $PFBase, resolveUITheme } from "@goauthentik/web/common/theme.js";

import { TemplateResult, render as litRender } from "lit";

/**
 * A special version of render that ensures our stylesheets:
 *
 * - Will always be available to all elements under test.
 * - Ensure they look right during testing.
 * - CSS-based checks for visibility will return correct values.
 */
export const render = (body: TemplateResult) => {
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

    return litRender(body, document.body);
};
