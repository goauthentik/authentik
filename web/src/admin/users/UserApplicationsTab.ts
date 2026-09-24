import "#admin/users/UserApplicationTable";
import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { AKElement } from "#elements/Base";

import { User } from "@goauthentik/api";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-applications-tab")
export class UserApplicationsTab extends AKElement {
    @property({ attribute: false })
    public user?: User;

    static styles = [PFCard];

    protected override render() {
        if (!this.user) {
            return nothing;
        }

        return html`<div class="pf-c-card">
            <ak-user-application-table .user=${this.user}></ak-user-application-table>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-applications-tab": UserApplicationsTab;
    }
}
