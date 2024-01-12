import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/Alert";
import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import { EnterpriseApi } from "@goauthentik/api";

@customElement("ak-license-notice")
export class AkLicenceNotice extends AKElement {
    @state()
    hasLicense = false;

    constructor() {
        super();
        new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseSummaryRetrieve().then((enterprise) => {
            this.hasLicense = enterprise.hasLicense;
        });
    }

    render() {
        return this.hasLicense
            ? nothing
            : html`
                  <ak-alert class="pf-c-radio__description" inline>
                      ${msg("Provider requires enterprise.")}
                      <a href="#/enterprise/licenses">${msg("Learn more")}</a>
                  </ak-alert>
              `;
    }
}
