import "#elements/ak-progress-bar";

import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import { LicenseForecast, LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFProgress from "@patternfly/patternfly/components/Progress/progress.css";
import PFSplit from "@patternfly/patternfly/layouts/Split/split.css";

const badgeDetails = new Map<LicenseSummaryStatusEnum | undefined, [PFColor, string]>([
    [LicenseSummaryStatusEnum.Expired, [PFColor.Red, msg("Expired")]],
    [LicenseSummaryStatusEnum.ExpirySoon, [PFColor.Orange, msg("Expiring soon")]],
    [LicenseSummaryStatusEnum.Unlicensed, [PFColor.Gray, msg("Unlicensed")]],
    [LicenseSummaryStatusEnum.ReadOnly, [PFColor.Red, msg("Read Only")]],
    [LicenseSummaryStatusEnum.LimitExceededAdmin, [PFColor.Orange, msg("User Count Exceeded")]],
    [LicenseSummaryStatusEnum.LimitExceededUser, [PFColor.Red, msg("User Count Exceeded")]],
    [LicenseSummaryStatusEnum.Valid, [PFColor.Green, msg("Valid")]],
]);

const Style = css`
    .pf-l-split {
        --pf-l-split--m-gutter--MarginRight: 3rem;
    }
`;

@customElement("ak-enterprise-status-card")
export class EnterpriseStatusCard extends AKElement {
    @property({ attribute: false })
    forecast?: LicenseForecast;

    @property({ attribute: false })
    summary?: LicenseSummary;

    static styles: CSSResult[] = [PFDescriptionList, PFCard, PFSplit, PFProgress, Style];

    renderSummaryBadge() {
        const status = badgeDetails.get(this.summary?.status);
        if (!status) return nothing;
        return html`<ak-label color=${status[0]}>${status[1]}</ak-label>`;
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
        const isLicensed = this.summary.status !== LicenseSummaryStatusEnum.Unlicensed;

        const progressBar = (label: string, current: number, licensed: number) => {
            const percentage = isLicensed ? this.calcUserPercentage(licensed, current) : 0;
            const severity = classMap({
                "pf-m-success": isLicensed && percentage <= 80,
                "pf-m-danger": isLicensed && percentage > 100,
                "pf-m-warning": isLicensed && percentage > 80 && percentage <= 100,
            });

            return html`
                <ak-progress-bar class="${severity}" value=${percentage}>
                    <span slot="description">${label} (${current} / ${licensed})</span>
                    <span slot="status"> ${percentage < Infinity ? `${percentage}` : "∞"}% </span>
                </ak-progress-bar>
            `;
        };

        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">${msg("Current license status")}</div>
            <div class="pf-c-card__body">
                <div class="pf-l-split pf-m-gutter">
                    <dl class="pf-l-split__item pf-c-description-list">
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
                        ${progressBar(
                            msg("Internal user usage"),
                            currentInternalUsers,
                            licensedInternalUsers,
                        )}
                        ${progressBar(
                            msg("External user usage"),
                            currentExternalUsers,
                            licensedExternalUsers,
                        )}
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
