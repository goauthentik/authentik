import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";

import { AKElement } from "#elements/Base";
import { WithLicenseSummary } from "#elements/mixins/license";
import { toAdminInterface } from "#elements/router/core/interfaces";

import { LicenseFlagsEnum, LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-enterprise-status")
export class EnterpriseStatusBanner extends WithLicenseSummary(AKElement) {
    @property()
    interface: "admin" | "user" | "flow" | "" = "";

    static styles = [PFBanner, PFFlex];

    renderStatusBanner() {
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

        const isDanger = this.licenseSummary?.status === LicenseSummaryStatusEnum.ReadOnly;

        return html`<div class="pf-c-banner pf-m-sticky ${isDanger ? "pf-m-red" : "pf-m-gold"}">
            <div class="pf-l-flex pf-m-space-items-sm">
                <div class="pf-l-flex__item">
                    <span class="sr-only">
                        ${isDanger ? msg("Danger banner:") : msg("Warning banner:")}
                    </span>
                    <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                </div>
                <div class="pf-l-flex__item">
                    ${message}
                    <a href=${toAdminInterface("enterprise/licenses")}>
                        ${msg("Click here for more info.")}
                    </a>
                </div>
            </div>
        </div>`;
    }

    renderFlagBanner() {
        return html`
            ${
                this.licenseSummary?.licenseFlags.includes(LicenseFlagsEnum.Trial)
                    ? html`<div class="pf-c-banner pf-m-sticky pf-m-gold">
                          <div class="pf-l-flex pf-m-space-items-sm">
                              <div class="pf-l-flex__item">
                                  <span class="sr-only">${msg("Warning banner:")}</span>
                                  <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                              </div>
                              <div class="pf-l-flex__item">
                                  ${msg("This authentik instance uses a Trial license.")}
                              </div>
                          </div>
                      </div>`
                    : nothing
            }
            ${
                this.licenseSummary?.licenseFlags.includes(LicenseFlagsEnum.NonProduction)
                    ? html`<div class="pf-c-banner pf-m-sticky pf-m-gold">
                          <div class="pf-l-flex pf-m-space-items-sm">
                              <div class="pf-l-flex__item">
                                  <span class="sr-only">${msg("Warning banner:")}</span>
                                  <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                              </div>
                              <div class="pf-l-flex__item">
                                  ${msg("This authentik instance uses a Non-production license.")}
                              </div>
                          </div>
                      </div>`
                    : nothing
            }
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
