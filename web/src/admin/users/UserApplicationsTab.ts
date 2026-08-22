import "#admin/users/UserApplicationEntitlementTable";
import "#admin/users/UserApplicationTable";
import "#elements/Tabs";

import { AKElement } from "#elements/Base";
import { WithLazyTabs } from "#elements/mixins/lazy-tabs";

import { User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-user-applications-tab")
export class UserApplicationsTab extends WithLazyTabs(AKElement) {
    @property({ attribute: false })
    public user?: User;

    public override activatedTabs = new Set<string>(["page-applications"]);

    static styles = [PFPage, PFCard];

    protected override render() {
        if (!this.user) {
            return nothing;
        }

        return html`<ak-tabs pageIdentifier="userApplications" vertical>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-applications"
                id="page-applications"
                aria-label=${msg("Applications")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
                @activate=${() => this.activateTab("page-applications")}
            >
                ${this.renderWhenActive(
                    "page-applications",
                    html`<div class="pf-c-card">
                        <ak-user-application-table .user=${this.user}></ak-user-application-table>
                    </div>`,
                )}
            </div>
            <div
                role="tabpanel"
                tabindex="0"
                slot="page-entitlements"
                id="page-entitlements"
                aria-label=${msg("Application entitlements")}
                class="pf-c-page__main-section pf-m-no-padding-mobile"
                @activate=${() => this.activateTab("page-entitlements")}
            >
                ${this.renderWhenActive(
                    "page-entitlements",
                    html`<div class="pf-c-card">
                        <ak-user-application-entitlement-table
                            .user=${this.user}
                        ></ak-user-application-entitlement-table>
                    </div>`,
                )}
            </div>
        </ak-tabs>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-applications-tab": UserApplicationsTab;
    }
}
