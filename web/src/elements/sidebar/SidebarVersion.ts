import type { AdminInterface } from "@goauthentik/admin/AdminInterface/AdminInterface";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { globalAK } from "@goauthentik/common/global";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";
import { DefaultBrand } from "@goauthentik/elements/sidebar/SidebarBrand";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AdminApi, LicenseSummaryStatusEnum, Version } from "@goauthentik/api";

@customElement("ak-sidebar-version")
export class SidebarVersion extends WithLicenseSummary(AKElement) {
    static get styles(): CSSResult[] {
        return [
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
    }

    @state()
    version?: Version;

    async firstUpdated() {
        this.version = await new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve();
    }

    render(): TemplateResult {
        let product = globalAK().brand.brandingTitle || DefaultBrand.brandingTitle;
        if (this.licenseSummary.status != LicenseSummaryStatusEnum.Unlicensed) {
            product += ` ${msg("Enterprise")}`;
        }
        return html`<button
            class="pf-c-button pf-m-plain"
            @click=${() => {
                const int = rootInterface<AdminInterface>();
                int?.aboutModal?.onClick();
            }}
        >
            <p class="pf-c-title">${product}</p>
            <p class="pf-c-title">${msg(str`Version ${this.version?.versionCurrent || ""}`)}</p>
        </button>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar-version": SidebarVersion;
    }
}
