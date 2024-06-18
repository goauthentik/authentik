import { AKElement } from "@goauthentik/elements/Base";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-enterprise-status")
export class EnterpriseStatusBanner extends WithLicenseSummary(AKElement) {
    @property()
    interface: "admin" | "user" | "" = "";

    static get styles(): CSSResult[] {
        return [PFBanner];
    }

    renderBanner(): TemplateResult {
        return html`<div
            class="pf-c-banner ${this.licenseSummary?.readOnly ? "pf-m-red" : "pf-m-gold"}"
        >
            ${msg("Warning: The current user count has exceeded the configured licenses.")}
            <a href="/if/admin/#/enterprise/licenses"> ${msg("Click here for more info.")} </a>
        </div>`;
    }

    render(): TemplateResult {
        switch (this.interface.toLowerCase()) {
            case "admin":
                if (this.licenseSummary?.showAdminWarning || this.licenseSummary?.readOnly) {
                    return this.renderBanner();
                }
                break;
            case "user":
                if (this.licenseSummary?.showUserWarning || this.licenseSummary?.readOnly) {
                    return this.renderBanner();
                }
                break;
        }
        return html``;
    }
}
