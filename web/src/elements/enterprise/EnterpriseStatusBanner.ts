import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import { EnterpriseApi, LicenseBody } from "@goauthentik/api";

@customElement("ak-enterprise-status")
export class EnterpriseStatusBanner extends AKElement {
    @state()
    body?: LicenseBody;

    static get styles(): CSSResult[] {
        return [PFBanner];
    }

    firstUpdated(): void {
        new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseIsValidRetrieve().then((b) => {
            this.body = b;
        });
    }

    render(): TemplateResult {
        return html`<div class="pf-c-banner pf-m-warning">
            ${msg(
                "Warning: No invitation stage is bound to any flow. Invitations will not work as expected.",
            )}
        </div>`;
    }
}
