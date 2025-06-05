import { applyDocumentTheme } from "@goauthentik/common/theme.js";

import { TemplateResult, render as litRender } from "lit";

/**
 * A special version of render that ensures our stylesheets:
 *
 * - Will always be available to all elements under test.
 * - Ensure they look right during testing.
 * - CSS-based checks for visibility will return correct values.
 */
export const render = (body: TemplateResult) => {
    applyDocumentTheme();

    return litRender(body, document.body);
};
