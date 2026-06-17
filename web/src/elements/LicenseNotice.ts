import "#elements/Alert";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { SlottedTemplateResult } from "#elements/types";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-license-notice")
export class AKLicenceNotice extends WithLicenseSummary(AKElement) {
    public static styles = [
        css`
            ::part(container) {
                background-color: transparent;
            }
        `,
    ];

    @property({ type: String })
    public label = msg("Enterprise only");

    @property({ type: String })
    public description = msg("Learn more about the enterprise license.");

    protected override render(): SlottedTemplateResult {
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
