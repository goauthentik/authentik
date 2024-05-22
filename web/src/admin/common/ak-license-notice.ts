import "@goauthentik/elements/Alert";
import { AKElement } from "@goauthentik/elements/Base";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-license-notice")
export class AkLicenceNotice extends WithLicenseSummary(AKElement) {
    @property()
    notice = msg("Enterprise only");

    render() {
        return this.hasEnterpriseLicense
            ? nothing
            : html`
                  <ak-alert class="pf-c-radio__description" inline plain>
                      <a href="#/enterprise/licenses">${this.notice}</a>
                  </ak-alert>
              `;
    }
}
