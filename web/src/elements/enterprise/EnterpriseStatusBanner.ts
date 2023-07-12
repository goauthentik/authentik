import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import { EnterpriseApi, LicenseBody } from "@goauthentik/api";

@customElement("ak-enterprise-status")
export class EnterpriseStatusBanner extends AKElement {
    @state()
    body?: LicenseBody;

    @property()
    interface: "admin" | "user" | "" = "";

    static get styles(): CSSResult[] {
        return [PFBanner];
    }

    firstUpdated(): void {
        new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseIsValidRetrieve().then((b) => {
            this.body = b;
        });
    }

    renderBanner(): TemplateResult {
        return html`<div class="pf-c-banner ${this.body?.readOnly ? "pf-m-red" : "pf-m-orange"}">
            ${msg("Warning: The current user count has exceeded the configured licenses.")}
            <a href="/if/admin/#/enterprise/licenses"> ${msg("Click here for more info.")} </a>
        </div>`;
    }

    render(): TemplateResult {
        switch (this.interface.toLowerCase()) {
            case "admin":
                if (this.body?.showAdminWarning || this.body?.readOnly) {
                    return this.renderBanner();
                }
                break;
            case "user":
                if (this.body?.showUserWarning || this.body?.readOnly) {
                    return this.renderBanner();
                }
                break;
        }
        return html``;
    }
}
