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

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";

@customElement("ak-sidebar-version")
export class SidebarVersion extends WithLicenseSummary(WithVersion(AKElement)) {
    static styles: CSSResult[] = [
        PFNav,
        PFAvatar,
        PFButton,
        css`
            :host {
                display: block;
            }
            footer {
                display: flex;
                width: 100%;
                flex-direction: column;
                justify-content: space-between;
                padding: 1rem !important;
            }
            p {
                text-align: center;
                width: 100%;
                font-size: var(--pf-global--FontSize--xs);
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
            <footer aria-label=${msg("authentik information")}>
                <button
                    part="trigger"
                    aria-label=${msg("Open about dialog")}
                    class="pf-c-button pf-m-plain"
                    @click=${AboutModal.open}
                >
                    <p
                        role="heading"
                        aria-level="1"
                        aria-description=${msg("Product name")}
                        id="sidebar-version-product"
                        class="pf-c-title"
                        part="button-content product-name"
                    >
                        ${product}
                    </p>
                    <p
                        role="heading"
                        aria-level="1"
                        aria-description=${msg("Product version")}
                        id="sidebar-version-product"
                        class="pf-c-title"
                        part="button-content product-version"
                    >
                        ${msg(str`Version ${this.version?.versionCurrent || ""}`)}
                    </p>
                </button>
            </footer>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar-version": SidebarVersion;
    }
}
