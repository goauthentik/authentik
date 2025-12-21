import "#elements/ak-progress-bar";

import { AKElement } from "#elements/Base";
import { PFColor } from "#elements/Label";

import { LicenseForecast, LicenseSummary, LicenseSummaryStatusEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFSplit from "@patternfly/patternfly/layouts/Split/split.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-enterprise-status-card")
export class EnterpriseStatusCard extends AKElement {
    @state()
    forecast?: LicenseForecast;

    @state()
    summary?: LicenseSummary;

    static styles: CSSResult[] = [PFBase, PFDescriptionList, PFCard, PFSplit];

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
                        <ak-progress-bar
                            class="${internalUserPercentage > 100
                                ? "pf-m-danger"
                                : ""} ${internalUserPercentage >= 80 ? "pf-m-warning" : ""}"
                            value=${internalUserPercentage}
                        >
                            <span slot="description">${msg("Internal user usage")}</span>
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
                            <span slot="description">${msg("External user usage")}</span>
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
