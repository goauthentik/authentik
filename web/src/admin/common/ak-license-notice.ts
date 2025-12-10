import "#elements/Alert";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-license-notice")
export class AKLicenceNotice extends WithLicenseSummary(AKElement) {
    @property()
    public label = msg("Enterprise only");

    @property()
    public description = msg("Learn more about the enterprise license.");

    render() {
        if (this.hasEnterpriseLicense) {
            return nothing;
        }

        return html`
            <ak-alert class="pf-c-radio__description" inline plain>
                <a
                    aria-label="${this.label}"
                    aria-description="${this.description}"
                    href="#/enterprise/licenses"
                    >${this.label}</a
                >
            </ak-alert>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-license-notice": AKLicenceNotice;
    }
}
