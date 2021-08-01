import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../../api/Client";
import { TablePage } from "../../../elements/table/TablePage";

import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteForm";
import "../../../elements/forms/ModalForm";
import "./InvitationForm";
import "./InvitationListLink";
import { TableColumn } from "../../../elements/table/Table";
import { PAGE_SIZE } from "../../../constants";
import { Invitation, StagesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";

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
            new TableColumn(""),
        ];
    }

    row(item: Invitation): TemplateResult[] {
        return [
            html`${item.pk}`,
            html`${item.createdBy?.username}`,
            html`${item.expires?.toLocaleString() || "-"}`,
            html`
            <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Invitation`}
                .usedBy=${() => {
                    return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsUsedByList({
                        inviteUuid: item.pk
                    });
                }}
                .delete=${() => {
                    return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsDestroy({
                        inviteUuid: item.pk
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${t`Delete`}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderExpanded(item: Invitation): TemplateResult {
        return html`
        <td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <ak-stage-invitation-list-link invitation=${item.pk}></ak-stage-invitation-list-link>
            </div>
        </td>
        <td></td>
        <td></td>
        <td></td>`;
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-forms-modal>
            <span slot="submit">
                ${t`Create`}
            </span>
            <span slot="header">
                ${t`Create Invitation`}
            </span>
            <ak-invitation-form slot="form">
            </ak-invitation-form>
            <button slot="trigger" class="pf-c-button pf-m-primary">
                ${t`Create`}
            </button>
        </ak-forms-modal>
        ${super.renderToolbar()}
        `;
    }
}
