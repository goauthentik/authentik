import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import { Invitation, StagesApi } from "@goauthentik/api";

import { AKResponse } from "../../../api/Client";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { uiConfig } from "../../../common/config";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteBulkForm";
import "../../../elements/forms/ModalForm";
import { TableColumn } from "../../../elements/table/Table";
import { TablePage } from "../../../elements/table/TablePage";
import "./InvitationForm";
import "./InvitationListLink";

@customElement("ak-stage-invitation-list")
export class InvitationListPage extends TablePage<Invitation> {
    expandable = true;

    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Invitations`;
    }
    pageDescription(): string {
        return t`Create Invitation Links to enroll Users, and optionally force specific attributes of their account.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-migration";
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(PFBanner);
    }

    checkbox = true;

    @property()
    order = "expires";

    @state()
    invitationStageExists = false;

    async apiEndpoint(page: number): Promise<AKResponse<Invitation>> {
        const stages = await new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesList({
            noFlows: false,
        });
        this.invitationStageExists = stages.pagination.count > 0;
        this.expandable = this.invitationStageExists;
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Created by`, "created_by"),
            new TableColumn(t`Expiry`),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Invitation(s)`}
            .objects=${this.selectedElements}
            .usedBy=${(item: Invitation) => {
                return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsUsedByList({
                    inviteUuid: item.pk,
                });
            }}
            .delete=${(item: Invitation) => {
                return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsDestroy({
                    inviteUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Invitation): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.createdBy?.username}`,
            html`${item.expires?.toLocaleString() || t`-`}`,
            html` <ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update Invitation`} </span>
                <ak-invitation-form slot="form" .instancePk=${item.pk}> </ak-invitation-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderExpanded(item: Invitation): TemplateResult {
        return html` <td role="cell" colspan="3">
                <div class="pf-c-table__expandable-row-content">
                    <ak-stage-invitation-list-link
                        invitation=${item.pk}
                    ></ak-stage-invitation-list-link>
                </div>
            </td>
            <td></td>
            <td></td>
            <td></td>`;
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Invitation`} </span>
                <ak-invitation-form slot="form"> </ak-invitation-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
        `;
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon=${this.pageIcon()}
                header=${this.pageTitle()}
                description=${ifDefined(this.pageDescription())}
            >
            </ak-page-header>
            ${this.invitationStageExists
                ? html``
                : html`
                      <div class="pf-c-banner pf-m-warning">
                          ${t`Warning: No invitation stage is bound to any flow. Invitations will not work as expected.`}
                      </div>
                  `}
            <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                <div class="pf-c-card">${this.renderTable()}</div>
            </section>`;
    }
}
