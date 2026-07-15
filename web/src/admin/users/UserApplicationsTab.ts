import "#admin/users/UserApplicationTable";

import { AKElement } from "#elements/Base";

import { User } from "@goauthentik/api";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

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
