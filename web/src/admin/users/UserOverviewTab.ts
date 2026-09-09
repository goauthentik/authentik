import "#admin/users/UserChart";
import "#admin/users/UserInfoCard";
import "#admin/users/UserNotesCard";
import "#components/ak-object-attributes-card";
import "#admin/events/ObjectChangelog";

import { AKElement } from "#elements/Base";

import { ModelEnum, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-user-overview-tab")
export class UserOverviewTab extends AKElement {
    @property({ attribute: false })
    public user?: User;

    @property({ type: Number })
    public currentUserPk?: number;

    @property({ type: Boolean })
    public canImpersonate = false;

    @property({ type: Boolean })
    public hasEnterpriseLicense = false;

    @property({ type: Boolean })
    public brandHasRecoveryFlow = false;

    static styles = [PFGrid, PFCard, PFContent];

    protected override render() {
        if (!this.user) {
            return nothing;
        }

        return html`<div class="pf-l-grid pf-m-gutter">
            <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-5-col-on-xl">
                <ak-user-info-card
                    .user=${this.user}
                    .currentUserPk=${this.currentUserPk}
                    .canImpersonate=${this.canImpersonate}
                    .hasEnterpriseLicense=${this.hasEnterpriseLicense}
                    .brandHasRecoveryFlow=${this.brandHasRecoveryFlow}
                ></ak-user-info-card>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-7-col-on-xl">
                <div class="pf-c-card__title">
                    ${msg("Actions over the last week (per 8 hours)")}
                </div>
                <div class="pf-c-card__body">
                    <ak-charts-user username=${this.user.username}></ak-charts-user>
                </div>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-5-col-on-xl">
                <ak-user-notes-card .notes=${this.user.attributes?.notes}></ak-user-notes-card>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-7-col-on-xl">
                <ak-object-attributes-card
                    .objectAttributes=${this.user.attributes}
                ></ak-object-attributes-card>
            </div>
            <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                <div class="pf-c-card__title">${msg("Changelog")}</div>
                <ak-object-changelog
                    targetModelPk=${this.user.pk}
                    targetModelName=${ModelEnum.AuthentikCoreUser}
                ></ak-object-changelog>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-overview-tab": UserOverviewTab;
    }
}
