import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";

import { LicenseFlagsEnum, LicenseStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-enterprise-status")
export class EnterpriseStatusBanner extends WithLicenseSummary(AKElement) {
    @property()
    interface: "admin" | "user" | "flow" | "" = "";

    static styles = [PFBanner];

    renderStatusBanner() {
        // Check if we're in the correct interface to render a banner
        switch (this.licenseSummary?.status) {
            // user warning is both on admin interface and user interface
            case LicenseStatusEnum.LimitExceededUser:
                if (
                    this.interface.toLowerCase() !== "user" &&
                    this.interface.toLowerCase() !== "admin"
                ) {
                    return nothing;
                }
                break;
            case LicenseStatusEnum.ExpirySoon:
            case LicenseStatusEnum.Expired:
            case LicenseStatusEnum.LimitExceededAdmin:
                if (this.interface.toLowerCase() !== "admin") {
                    return nothing;
                }
                break;
            case LicenseStatusEnum.Unlicensed:
            case LicenseStatusEnum.Valid:
                return nothing;
            case LicenseStatusEnum.ReadOnly:
            default:
                break;
        }
        let message = "";
        switch (this.licenseSummary?.status) {
            case LicenseStatusEnum.LimitExceededAdmin:
            case LicenseStatusEnum.LimitExceededUser:
                message = msg(
                    "Warning: The current user count has exceeded the configured licenses.",
                );
                break;
            case LicenseStatusEnum.Expired:
                message = msg("Warning: One or more license(s) have expired.");
                break;
            case LicenseStatusEnum.ExpirySoon:
                message = msg(
                    "Warning: One or more license(s) will expire within the next 2 weeks.",
                );
                break;
            case LicenseStatusEnum.ReadOnly:
                message = msg(
                    "Caution: This authentik instance has entered read-only mode due to expired/exceeded licenses.",
                );
                break;
            default:
                break;
        }
        return html`<div
            class="pf-c-banner pf-m-sticky ${this.licenseSummary?.status ===
            LicenseStatusEnum.ReadOnly
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
