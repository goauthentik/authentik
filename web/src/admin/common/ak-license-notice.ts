import "#elements/Alert";

import { $PFBase } from "#common/theme";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-license-notice")
export class AkLicenceNotice extends WithLicenseSummary(AKElement) {
    static styles = [$PFBase];

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

declare global {
    interface HTMLElementTagNameMap {
        "ak-license-notice": AkLicenceNotice;
    }
}
