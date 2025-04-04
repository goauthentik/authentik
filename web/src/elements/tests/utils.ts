import { TemplateResult, render as litRender } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ensureCSSStyleSheet } from "../utils/ensureCSSStyleSheet.js";

/**
 * A special version of Lit's render that ensures...
 *
 * - Our style sheets will always be available to all elements under test.
 * - The body will always have the correct styles applied.
 * - CSS-based checks for visibility will return correct values.
 *
 * @todo Do we need to add a `documentLike` parameter to this function?
 */
export function render(body: TemplateResult, documentLike: Document = document) {
    documentLike.adoptedStyleSheets = [
        ...documentLike.adoptedStyleSheets,
        ensureCSSStyleSheet(PFBase),
        ensureCSSStyleSheet(AKGlobal),
    ];

    return litRender(body, documentLike.body);
}
