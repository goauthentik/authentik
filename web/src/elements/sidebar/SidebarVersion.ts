import { globalAK } from "#common/global";
import { rootInterface } from "#common/theme";
import { DefaultBrand } from "#common/ui/config";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { WithVersion } from "#elements/mixins/version";

import type { AdminInterface } from "#admin/AdminInterface/index.entrypoint";

import { LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-sidebar-version")
export class SidebarVersion extends WithLicenseSummary(WithVersion(AKElement)) {
    static styles: CSSResult[] = [
        PFBase,
        PFNav,
        PFAvatar,
        PFButton,
        css`
            :host {
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
        return html`<button
            part="trigger"
            role="contentinfo"
            aria-label=${msg("Open about dialog")}
            class="pf-c-button pf-m-plain"
            @click=${() => {
                const int = rootInterface<AdminInterface>();
                int?.aboutModal?.show();
            }}
        >
            <p
                role="heading"
                aria-level="1"
                aria-label=${msg("Product name")}
                id="sidebar-version-product"
                class="pf-c-title"
                part="button-content product-name"
            >
                ${product}
            </p>
            <p
                role="heading"
                aria-level="1"
                aria-label=${msg("Product version")}
                id="sidebar-version-product"
                class="pf-c-title"
                part="button-content product-version"
            >
                ${msg(str`Version ${this.version?.versionCurrent || ""}`)}
            </p>
        </button>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar-version": SidebarVersion;
    }
}
