import { t } from "@lingui/macro";

import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators";

import { Invitation, StagesApi } from "@goauthentik/api";

import { AKResponse } from "../../../api/Client";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { PAGE_SIZE } from "../../../constants";
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

    checkbox = true;

    @property()
    order = "expires";

    apiEndpoint(page: number): Promise<AKResponse<Invitation>> {
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`ID`, "pk"),
            new TableColumn(t`Created by`, "created_by"),
            new TableColumn(t`Expiry`),
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
            html`${item.pk}`,
            html`${item.createdBy?.username}`,
            html`${item.expires?.toLocaleString() || t`-`}`,
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

    renderToolbar(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Invitation`} </span>
                <ak-invitation-form slot="form"> </ak-invitation-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
            ${super.renderToolbar()}
        `;
    }
}
