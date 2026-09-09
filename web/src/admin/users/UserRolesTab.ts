import "#admin/roles/ak-related-role-table";
import "#elements/Tabs";

import { AKElement } from "#elements/Base";
import { WithLazyTabs } from "#elements/mixins/lazy-tabs";

import { User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-user-roles-tab")
export class UserRolesTab extends WithLazyTabs(AKElement) {
    @property({ attribute: false })
    public user?: User;

    public override activatedTabs = new Set<string>(["page-assigned-roles"]);

    static styles = [PFPage, PFCard];

    protected override render() {
        if (!this.user) {
            return nothing;
        }

        return html`<ak-tabs pageIdentifier="userRoles" vertical>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-assigned-roles"
                id="page-assigned-roles"
                aria-label=${msg("Assigned Roles")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
                @activate=${() => this.activateTab("page-assigned-roles")}
            >
                ${this.renderWhenActive(
                    "page-assigned-roles",
                    html`<div class="pf-c-card">
                        <ak-related-role-table .targetUser=${this.user}></ak-related-role-table>
                    </div>`,
                )}
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-all-roles"
                id="page-all-roles"
                aria-label=${msg("All Roles")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
                @activate=${() => this.activateTab("page-all-roles")}
            >
                ${this.renderWhenActive(
                    "page-all-roles",
                    html`<div class="pf-c-card">
                        <ak-related-role-table
                            .targetUser=${this.user}
                            showInherited
                        ></ak-related-role-table>
                    </div>`,
                )}
            </div>
        </ak-tabs>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-roles-tab": UserRolesTab;
    }
}
