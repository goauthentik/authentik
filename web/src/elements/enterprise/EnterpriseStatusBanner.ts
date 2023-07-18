import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import { EnterpriseApi, LicenseSummary } from "@goauthentik/api";

@customElement("ak-enterprise-status")
export class EnterpriseStatusBanner extends AKElement {
    @state()
    summary?: LicenseSummary;

    @property()
    interface: "admin" | "user" | "" = "";

    static get styles(): CSSResult[] {
        return [PFBanner];
    }

    firstUpdated(): void {
        new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseSummaryRetrieve().then((b) => {
            this.summary = b;
        });
    }

    renderBanner(): TemplateResult {
        return html`<div class="pf-c-banner ${this.summary?.readOnly ? "pf-m-red" : "pf-m-gold"}">
            ${msg("Warning: The current user count has exceeded the configured licenses.")}
            <a href="/if/admin/#/enterprise/licenses"> ${msg("Click here for more info.")} </a>
        </div>`;
    }

    render(): TemplateResult {
        switch (this.interface.toLowerCase()) {
            case "admin":
                if (this.summary?.showAdminWarning || this.summary?.readOnly) {
                    return this.renderBanner();
                }
                break;
            case "user":
                if (this.summary?.showUserWarning || this.summary?.readOnly) {
                    return this.renderBanner();
                }
                break;
        }
        return html``;
    }
}
