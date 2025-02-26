import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

/**
 * Library Page Application List Empty
 *
 * Display a message if there are no applications defined in the current instance. If the user is an
 * administrator, provide a link to the "Create a new application" page.
 */

@customElement("ak-library-application-search-empty")
export class LibraryPageApplicationSearchEmpty extends AKElement {
    static get styles() {
        return [PFBase, PFEmptyState, PFContent, PFSpacing];
    }

    render() {
        return html` <div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <i class="fas fa-cubes pf-c-empty-state__icon" aria-hidden="true"></i>
                <h1 class="pf-c-title pf-m-lg">${msg("Search returned no results.")}</h1>
            </div>
        </div>`;
    }
}
