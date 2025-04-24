import {
    appendStyleSheet,
    assertAdoptableStyleSheetParent,
} from "@goauthentik/common/stylesheets.js";

import { TemplateResult, render as litRender } from "lit";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

// A special version of render that ensures our style sheets will always be available
// to all elements under test.  Ensures they look right during testing, and that any
// CSS-based checks for visibility will return correct values.

export const render = (body: TemplateResult) => {
    assertAdoptableStyleSheetParent(document);

    appendStyleSheet([PFBase, AKGlobal], document);
    return litRender(body, document.body);
};
