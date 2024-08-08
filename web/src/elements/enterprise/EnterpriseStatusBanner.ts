import { AKElement } from "@goauthentik/elements/Base";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import { LicenseSummaryStatusEnum } from "@goauthentik/api";

@customElement("ak-enterprise-status")
export class EnterpriseStatusBanner extends WithLicenseSummary(AKElement) {
    @property()
    interface: "admin" | "user" | "" = "";

    static get styles(): CSSResult[] {
        return [PFBanner];
    }

    renderBanner(): TemplateResult {
        let message = "";
        switch (this.licenseSummary.status) {
            case LicenseSummaryStatusEnum.LimitExceededAdmin:
            case LicenseSummaryStatusEnum.LimitExceededUser:
                message = msg(
                    "Warning: The current user count has exceeded the configured licenses.",
                );
                break;
            case LicenseSummaryStatusEnum.Expired:
                message = msg("Warning: One or more license(s) have expired.");
                break;
            case LicenseSummaryStatusEnum.ExpirySoon:
                message = msg(
                    "Warning: One or more license(s) will expire within the next 2 weeks.",
                );
                break;
            case LicenseSummaryStatusEnum.ReadOnly:
                message = msg(
                    "Caution: This authentik instance has entered read-only mode due to expired/exceeded licenses.",
                );
                break;
            default:
                break;
        }
        return html`<div
            class="pf-c-banner ${this.licenseSummary?.status === LicenseSummaryStatusEnum.ReadOnly
                ? "pf-m-red"
                : "pf-m-gold"}"
        >
            ${message}
            <a href="/if/admin/#/enterprise/licenses"> ${msg("Click here for more info.")} </a>
        </div>`;
    }

    render(): TemplateResult {
        switch (this.licenseSummary.status) {
            case LicenseSummaryStatusEnum.LimitExceededUser:
                if (this.interface.toLowerCase() === "user") {
                    return this.renderBanner();
                }
                break;
            case LicenseSummaryStatusEnum.ExpirySoon:
            case LicenseSummaryStatusEnum.Expired:
            case LicenseSummaryStatusEnum.LimitExceededAdmin:
                if (this.interface.toLowerCase() === "admin") {
                    return this.renderBanner();
                }
                break;
            case LicenseSummaryStatusEnum.ReadOnly:
                return this.renderBanner();
            default:
                break;
        }
        return html``;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enterprise-status": EnterpriseStatusBanner;
    }
}
