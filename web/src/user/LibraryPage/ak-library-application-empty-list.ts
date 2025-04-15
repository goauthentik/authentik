import { docLink, globalAK } from "@goauthentik/common/global";
import { AKElement } from "@goauthentik/elements/Base";
import { paramURL } from "@goauthentik/elements/router/RouterOutlet";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
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

@customElement("ak-library-application-empty-list")
export class LibraryPageApplicationEmptyList extends AKElement {
    static get styles() {
        return [
            PFBase,
            PFEmptyState,
            PFButton,
            PFContent,
            PFSpacing,
            css`
                .cta {
                    display: inline-block;
                    font-weight: bold;
                }
            `,
        ];
    }

    @property({ attribute: "isadmin", type: Boolean })
    isAdmin = false;

    renderNewAppButton() {
        const href = paramURL("/core/applications", {
            createWizard: true,
        });
        return html`
            <div class="pf-u-pt-lg">
                <a
                    aria-disabled="false"
                    class="cta pf-c-button pf-m-secondary"
                    href="${globalAK().api.base}if/admin/${href}"
                    >${msg("Create a new application")}</a
                >
            </div>
            <div class="pf-c-empty-state__body">
                <a rel="noopener noreferrer" href="${docLink("/docs/applications")}" target="_blank"
                    >${msg("Refer to documentation")}</a
                >
            </div>
        `;
    }

    render() {
        return html` <div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <i class="fas fa-cubes pf-c-empty-state__icon" aria-hidden="true"></i>
                <h1 class="pf-c-title pf-m-lg">${msg("No Applications available.")}</h1>
                <div class="pf-c-empty-state__body">
                    ${msg("Either no applications are defined, or you don’t have access to any.")}
                </div>
                ${this.isAdmin ? this.renderNewAppButton() : html``}
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library-application-empty-list": LibraryPageApplicationEmptyList;
    }
}
