import { globalAK } from "@goauthentik/common/global";
import { AKElement } from "@goauthentik/elements/Base";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import { LicenseFlagsEnum, LicenseSummaryStatusEnum } from "@goauthentik/api";

@customElement("ak-enterprise-status")
export class EnterpriseStatusBanner extends WithLicenseSummary(AKElement) {
    @property()
    interface: "admin" | "user" | "flow" | "" = "";

    static get styles() {
        return [PFBanner];
    }

    renderStatusBanner() {
        if (!this.licenseSummary) {
            return nothing;
        }
        // Check if we're in the correct interface to render a banner
        switch (this.licenseSummary?.status) {
            // user warning is both on admin interface and user interface
            case LicenseSummaryStatusEnum.LimitExceededUser:
                if (
                    this.interface.toLowerCase() !== "user" &&
                    this.interface.toLowerCase() !== "admin"
                ) {
                    return nothing;
                }
                break;
            case LicenseSummaryStatusEnum.ExpirySoon:
            case LicenseSummaryStatusEnum.Expired:
            case LicenseSummaryStatusEnum.LimitExceededAdmin:
                if (this.interface.toLowerCase() !== "admin") {
                    return nothing;
                }
                break;
            case LicenseSummaryStatusEnum.Unlicensed:
            case LicenseSummaryStatusEnum.Valid:
                return nothing;
            case LicenseSummaryStatusEnum.ReadOnly:
            default:
                break;
        }
        let message = "";
        switch (this.licenseSummary?.status) {
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
            class="pf-c-banner pf-m-sticky ${this.licenseSummary?.status ===
            LicenseSummaryStatusEnum.ReadOnly
                ? "pf-m-red"
                : "pf-m-gold"}"
        >
            ${message}
            <a href="${globalAK().api.base}if/admin/#/enterprise/licenses"
                >${msg("Click here for more info.")}</a
            >
        </div>`;
    }

    renderFlagBanner() {
        if (!this.licenseSummary) {
            return nothing;
        }
        return html`
            ${this.licenseSummary?.licenseFlags.includes(LicenseFlagsEnum.Trial)
                ? html`<div class="pf-c-banner pf-m-sticky pf-m-gold">
                      ${msg("This authentik instance uses a Trial license.")}
                  </div>`
                : nothing}
            ${this.licenseSummary?.licenseFlags.includes(LicenseFlagsEnum.NonProduction)
                ? html`<div class="pf-c-banner pf-m-sticky pf-m-gold">
                      ${msg("This authentik instance uses a Non-production license.")}
                  </div>`
                : nothing}
        `;
    }

    render() {
        return this.licenseSummary
            ? html`${this.renderFlagBanner()}${this.renderStatusBanner()}`
            : nothing;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enterprise-status": EnterpriseStatusBanner;
    }
}
