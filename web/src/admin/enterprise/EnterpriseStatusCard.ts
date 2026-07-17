import "#elements/ak-progress-bar";

import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import { LicenseForecast, LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFProgress from "@patternfly/patternfly/components/Progress/progress.css";
import PFSplit from "@patternfly/patternfly/layouts/Split/split.css";

const badgeDetails = {
    [LicenseSummaryStatusEnum.Expired]: [PFColor.Red, msg("Expired")],
    [LicenseSummaryStatusEnum.ExpirySoon]: [PFColor.Orange, msg("Expiring soon")],
    [LicenseSummaryStatusEnum.Unlicensed]: [PFColor.Gray, msg("Unlicensed")],
    [LicenseSummaryStatusEnum.ReadOnly]: [PFColor.Red, msg("Read Only")],
    [LicenseSummaryStatusEnum.LimitExceededAdmin]: [PFColor.Orange, msg("User Count Exceeded")],
    [LicenseSummaryStatusEnum.LimitExceededUser]: [PFColor.Red, msg("User Count Exceeded")],
    [LicenseSummaryStatusEnum.Valid]: [PFColor.Green, msg("Valid")],
    [LicenseSummaryStatusEnum.UnknownDefaultOpenApi]: [null, null],
};

@customElement("ak-enterprise-status-card")
export class EnterpriseStatusCard extends AKElement {
    @property({ attribute: false })
    forecast?: LicenseForecast;

    @property({ attribute: false })
    summary?: LicenseSummary;

    static styles: CSSResult[] = [PFDescriptionList, PFCard, PFSplit, PFProgress];

    renderSummaryBadge() {
        const status = this.summary?.status ?? LicenseSummaryStatusEnum.UnknownDefaultOpenApi;
        const [color, message] = badgeDetails[status] ?? [null, null];
        return color ? html`<ak-label color=${color}>${message}</ak-label>` : nothing;
    }

    calcUserPercentage(licensed: number, current: number) {
        const percentage = licensed > 0 ? Math.ceil(current / (licensed / 100)) : 0;
        if (current > 0 && licensed === 0) return Infinity;
        return percentage;
    }

    render() {
        if (!this.forecast || !this.summary) {
            return html`${msg("Loading")}`;
        }

        // Actual current usage counts (not the forecasted/projected fields).
        const currentInternalUsers = this.forecast.internalUsers;
        const currentExternalUsers = this.forecast.externalUsers;
        const licensedInternalUsers = this.summary.internalUsers;
        const licensedExternalUsers = this.summary.externalUsers;

        let internalUserPercentage = 0;
        let externalUserPercentage = 0;
        if (this.summary.status !== LicenseSummaryStatusEnum.Unlicensed) {
            internalUserPercentage = this.calcUserPercentage(
                licensedInternalUsers,
                currentInternalUsers,
            );
            externalUserPercentage = this.calcUserPercentage(
                licensedExternalUsers,
                currentExternalUsers,
            );
        }
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">${msg("Current license status")}</div>
            <div class="pf-c-card__body">
                <div class="pf-l-split pf-m-gutter">
                    <dl class="pf-l-split__item pf-c-description-list pf-m-horizontal">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${msg("Overall license status")}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${this.renderSummaryBadge()}
                                </div>
                            </dd>
                        </div>
                    </dl>
                    <div class="pf-l-split__item pf-m-fill">
                        <ak-progress-bar
                            class="${internalUserPercentage > 100
                                ? "pf-m-danger"
                                : ""} ${internalUserPercentage >= 80 ? "pf-m-warning" : ""}"
                            value=${internalUserPercentage}
                        >
                            <span slot="description">
                                ${msg(
                                    str`Internal user usage (${currentInternalUsers}/${licensedInternalUsers})`,
                                )}
                            </span>
                            <span slot="status">
                                ${msg(
                                    str`${internalUserPercentage < Infinity ? internalUserPercentage : "∞"}%`,
                                )}
                            </span>
                        </ak-progress-bar>
                        <ak-progress-bar
                            class="${externalUserPercentage > 100
                                ? "pf-m-danger"
                                : ""} ${externalUserPercentage >= 80 ? "pf-m-warning" : ""}"
                            value=${externalUserPercentage}
                        >
                            <span slot="description">
                                ${msg(
                                    str`External user usage (${currentExternalUsers}/${licensedExternalUsers})`,
                                )}
                            </span>
                            <span slot="status">
                                ${msg(
                                    str`${externalUserPercentage < Infinity ? externalUserPercentage : "∞"}%`,
                                )}
                            </span>
                        </ak-progress-bar>
                    </div>
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enterprise-status-card": EnterpriseStatusCard;
    }
}
