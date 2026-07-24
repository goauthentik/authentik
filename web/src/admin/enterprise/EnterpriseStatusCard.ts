/**
 * @file Display the current usage and license status of Enterprise licenses.
 */

import "#elements/Progress";
import "#elements/Label";

import { AKElement } from "#elements/Base";
import { ifPresent } from "#elements/utils/attributes";

import { LicenseForecast, LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

import { differenceInSeconds, formatDistanceStrict } from "date-fns";
import { match } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFSplit from "@patternfly/patternfly/layouts/Split/split.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";

const badgeDetails = new Map<LicenseSummaryStatusEnum, [string, string]>([
    [LicenseSummaryStatusEnum.Expired, ["red", msg("Expired")]],
    [LicenseSummaryStatusEnum.ExpirySoon, ["orange", msg("Expiring soon")]],
    [LicenseSummaryStatusEnum.Unlicensed, ["gray", msg("Unlicensed")]],
    [LicenseSummaryStatusEnum.ReadOnly, ["red", msg("Read Only")]],
    [LicenseSummaryStatusEnum.LimitExceededAdmin, ["orange", msg("User Count Exceeded")]],
    [LicenseSummaryStatusEnum.LimitExceededUser, ["red", msg("User Count Exceeded")]],
    [LicenseSummaryStatusEnum.Valid, ["green", msg("Valid")]],
]);

const Styles = css`
    .pf-c-card {
        container-type: inline-size;
        container-name: enterprise-status-card;
    }

    .pf-l-split {
        --pf-l-split--m-gutter--MarginRight: 1.5rem;
    }

    @container enterprise-status-card (width >= 480px) {
        .pf-l-split {
            --pf-l-split--m-gutter--MarginRight: 3rem;
        }
    }
`;

const DAY_IN_SECONDS = 86400;

@customElement("ak-enterprise-status-card")
export class EnterpriseStatusCard extends AKElement {
    static readonly styles: CSSResult[] = [PFDescriptionList, PFCard, PFSplit, PFStack, Styles];

    @property({ attribute: false })
    public forecast?: LicenseForecast;

    @property({ attribute: false })
    public summary?: LicenseSummary;

    protected renderSummaryBadge() {
        const summary = this.summary?.status;
        if (!summary) return nothing;

        const status = badgeDetails.get(summary);
        if (!status) return nothing;

        const valid = this.summary?.latestValid;
        const today = new Date();
        if (summary === LicenseSummaryStatusEnum.ExpirySoon && valid) {
            const gap = differenceInSeconds(valid, today);
            // prettier-ignore
            status[1] = match(gap)
                .when((g) => g < 0, () => status[1])
                .when((g) => g > 0 && g < DAY_IN_SECONDS, () => msg("Expiring today"))
                .otherwise(() => msg(
                    str`Expiring in ${formatDistanceStrict(new Date(), valid, { unit: "day" })}`))
        }

        return html`<ak-label color=${status[0]}>${status[1]}</ak-label>`;
    }

    protected calcUserPercentage(licensed: number, current: number) {
        const percentage = licensed > 0 ? Math.ceil(current / (licensed / 100)) : 0;
        if (current > 0 && licensed === 0) return Infinity;
        return percentage;
    }

    public override render() {
        if (!this.forecast || !this.summary) {
            return html`${msg("Loading")}`;
        }

        // Actual current usage counts (not the forecasted/projected fields).
        const currentInternalUsers = this.forecast.internalUsers;
        const currentExternalUsers = this.forecast.externalUsers;
        const licensedInternalUsers = this.summary.internalUsers;
        const licensedExternalUsers = this.summary.externalUsers;
        const licensed = this.summary.status !== LicenseSummaryStatusEnum.Unlicensed;

        const progressBar = (label: string, current: number, allowed: number) => {
            const percentage = licensed ? this.calcUserPercentage(allowed, current) : 0;
            // prettier-ignore
            const severity = licensed
                ? match(percentage)
                    .when((p) => p <= 80, () => "success")
                    .when((p) => p > 80 && p <= 100, () => "warning")
                    .otherwise(() => "danger")
                : null;

            return html`
                <ak-progress value=${percentage} severity=${ifPresent(severity)}>
                    <span slot="label">${label} (${current} / ${allowed})</span>
                    <span slot="status"> ${percentage < Infinity ? `${percentage}` : "∞"}% </span>
                </ak-progress>
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
                        <div class="pf-l-stack pf-m-gutter">
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
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enterprise-status-card": EnterpriseStatusCard;
    }
}
