import { AKElement } from "@goauthentik/elements/Base";
import { PFColor } from "@goauthentik/elements/Label";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFProgress from "@patternfly/patternfly/components/Progress/progress.css";
import PFSplit from "@patternfly/patternfly/layouts/Split/split.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { LicenseForecast, LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

@customElement("ak-enterprise-status-card")
export class EnterpriseStatusCard extends AKElement {
    @state()
    forecast?: LicenseForecast;

    @state()
    summary?: LicenseSummary;

    static get styles(): CSSResult[] {
        return [PFBase, PFDescriptionList, PFCard, PFSplit, PFProgress];
    }

    renderSummaryBadge() {
        switch (this.summary?.status) {
            case LicenseSummaryStatusEnum.Expired:
                return html`<ak-label color=${PFColor.Red}>${msg("Expired")}</ak-label>`;
            case LicenseSummaryStatusEnum.ExpirySoon:
                return html`<ak-label color=${PFColor.Orange}>${msg("Expiring soon")}</ak-label>`;
            case LicenseSummaryStatusEnum.Unlicensed:
                return html`<ak-label color=${PFColor.Grey}>${msg("Unlicensed")}</ak-label>`;
            case LicenseSummaryStatusEnum.ReadOnly:
                return html`<ak-label color=${PFColor.Red}>${msg("Read Only")}</ak-label>`;
            case LicenseSummaryStatusEnum.Valid:
                return html`<ak-label color=${PFColor.Green}>${msg("Valid")}</ak-label>`;
            default:
                return nothing;
        }
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
        let internalUserPercentage = 0;
        let externalUserPercentage = 0;
        if (this.summary.status !== LicenseSummaryStatusEnum.Unlicensed) {
            internalUserPercentage = this.calcUserPercentage(
                this.summary.internalUsers,
                this.forecast.internalUsers,
            );
            externalUserPercentage = this.calcUserPercentage(
                this.summary.externalUsers,
                this.forecast.externalUsers,
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
                        <div
                            class="pf-c-progress ${internalUserPercentage > 100
                                ? "pf-m-danger"
                                : ""} ${internalUserPercentage >= 80 ? "pf-m-warning" : ""}"
                            id="internalUsers"
                        >
                            <div class="pf-c-progress__description">
                                ${msg("Internal user usage")}
                            </div>
                            <div class="pf-c-progress__status" aria-hidden="true">
                                <span class="pf-c-progress__measure"
                                    >${msg(
                                        str`${internalUserPercentage < Infinity ? internalUserPercentage : "∞"}%`,
                                    )}</span
                                >
                            </div>
                            <div
                                class="pf-c-progress__bar"
                                role="progressbar"
                                aria-valuemin="0"
                                aria-valuemax="100"
                                aria-valuenow="${internalUserPercentage}"
                            >
                                <div
                                    class="pf-c-progress__indicator"
                                    style="width:${Math.min(internalUserPercentage, 100)}%;"
                                ></div>
                            </div>
                        </div>
                        <div
                            class="pf-c-progress ${externalUserPercentage > 100
                                ? "pf-m-danger"
                                : ""} ${externalUserPercentage >= 80 ? "pf-m-warning" : ""}"
                            id="externalUsers"
                        >
                            <div class="pf-c-progress__description">
                                ${msg("External user usage")}
                            </div>
                            <div class="pf-c-progress__status" aria-hidden="true">
                                <span class="pf-c-progress__measure"
                                    >${msg(
                                        str`${externalUserPercentage < Infinity ? externalUserPercentage : "∞"}%`,
                                    )}</span
                                >
                            </div>
                            <div
                                class="pf-c-progress__bar"
                                role="progressbar"
                                aria-valuemin="0"
                                aria-valuemax="100"
                                aria-valuenow="${externalUserPercentage < Infinity
                                    ? externalUserPercentage
                                    : "∞"}"
                            >
                                <div
                                    class="pf-c-progress__indicator"
                                    style="width:${Math.min(externalUserPercentage, 100)}%;"
                                ></div>
                            </div>
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
