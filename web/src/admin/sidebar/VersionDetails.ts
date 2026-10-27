import PFButton from "@patternfly/patternfly/components/Button/button.css";

import { globalAK } from "#common/global";
import { DefaultBrand } from "#common/ui/config";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithVersion } from "#elements/mixins/version";

import { AboutModal } from "#admin/ak-about-modal";

import { LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-version-details")
export class VersionDetails extends WithLicenseSummary(WithVersion(AKElement)) {
    static styles: CSSResult[] = [
        PFButton,
        css`
            :host {
                display: flex;
                width: 100%;
                flex-direction: column;
                justify-content: space-between;
                padding: 1rem;
            }
            [part~="product-info"] {
                display: block;
                text-align: center;
                width: 100%;
                font-size: var(--pf-global--FontSize--xs);
            }
            [part~="trigger"] {
                --pf-c-button--m-plain--hover--Color: var(--pf-c-nav__link--Color);
            }
        `,
    ];

    render() {
        if (!this.version || !this.licenseSummary) {
            return nothing;
        }

        let product = globalAK().brand.brandingTitle || DefaultBrand.brandingTitle;

        if (this.licenseSummary.status !== LicenseSummaryStatusEnum.Unlicensed) {
            product += ` ${msg("Enterprise")}`;
        }

        return html`
            <button
                part="trigger"
                type="button"
                aria-haspopup="dialog"
                class="pf-c-button pf-m-plain"
                @click=${AboutModal.open}
            >
                <span part="product-info product-name"> ${product} </span>
                <span part="product-info product-version">
                    ${msg(str`Version ${this.version?.versionCurrent}`)}
                </span>
            </button>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-version-details": VersionDetails;
    }
}
