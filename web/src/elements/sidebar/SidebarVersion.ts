import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { globalAK } from "@goauthentik/common/global";
import { AKElement } from "@goauthentik/elements/Base";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
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
        let product = globalAK().brand.brandingTitle;
        if (this.licenseSummary.status != LicenseSummaryStatusEnum.Unlicensed) {
            product += ` ${msg("Enterprise")}`;
        }
        return html`<p class="pf-c-title">${product}</p>
            <p class="pf-c-title">${msg(str`Version ${this.version?.versionCurrent}`)}</p> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar-version": SidebarVersion;
    }
}
