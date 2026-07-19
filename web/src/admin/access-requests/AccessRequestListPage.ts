import "#components/ak-status-label";
import "#elements/forms/ConfirmationForm";

import { aki } from "#common/api/client";
import { PaginatedResponse } from "#common/api/responses";

import { modalInvoker } from "#elements/dialogs";
import { RowType, Timestamp } from "#elements/table/Table";
import { TableColumn } from "#elements/table/TableColumn";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { AccessRequestFulfillForm } from "#admin/access-requests/AccessRequestFulfillForm";
import { renderTargetSummary } from "#admin/access-requests/RequestableTargetHelpers";

import { GrantRequest, PamApi, RequestStatus } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit-html";
import { customElement } from "lit/decorators.js";

function statusLabel(status: RequestStatus): string {
    switch (status) {
        case RequestStatus.Approved:
            return msg("Active");
        case RequestStatus.Denied:
            return msg("Denied");
        case RequestStatus.Revoked:
            return msg("Revoked");
        default:
            return msg("Pending");
    }
}

@customElement("ak-access-requests-list")
export class AccessRequestListPage extends TablePage<GrantRequest> {
    public pageTitle: string = msg("Access Requests");
    public pageDescription: string = msg("");
    public pageIcon: string = "";
    public expandable: boolean = true;
    public searchEnabled: boolean = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<GrantRequest, object>> {
        return aki(PamApi).pamGrantRequestsList({
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected columns: TableColumn[] = [
        [msg("User"), "createdBy"],
        [msg("Created"), "created"],
        [msg("Apps")],
        [msg("Status"), "status"],
        [msg("Actions")],
    ];

    protected renderExpanded(item: GrantRequest): SlottedTemplateResult {
        return html`${JSON.stringify(item.requesterData)}<br />${item.targets}`;
    }

    renderActions(item: GrantRequest): SlottedTemplateResult {
        if (item.status === RequestStatus.Created) {
            return html`<button
                class="pf-c-button pf-m-secondary pf-m-block"
                ${modalInvoker(AccessRequestFulfillForm, {
                    request: item,
                })}
            >
                ${msg("Fulfill")}
            </button>`;
        }
        if (item.isActive) {
            return html`<ak-forms-confirm
                successMessage=${msg("Successfully revoked grant")}
                errorMessage=${msg("Failed to revoke grant")}
                action=${msg("Revoke")}
                .onConfirm=${() => {
                    return aki(PamApi).pamGrantRequestsRevokeCreate({ uuid: item.uuid || "" });
                }}
            >
                <span slot="header">${msg("Revoke grant")}</span>
                <p slot="body">
                    ${msg(
                        "Are you sure you want to revoke this grant? Access will be removed immediately.",
                    )}
                </p>
                <button slot="trigger" class="pf-c-button pf-m-danger" type="button">
                    ${msg("Revoke")}
                </button>
            </ak-forms-confirm>`;
        }
        return nothing;
    }

    protected row(item: GrantRequest): RowType[] {
        return [
            html`<a href="#/identity/users/${item.createdBy.pk}">
                <div>${item.createdBy.username}</div>
                <small>${item.createdBy.name}</small>
            </a>`,
            Timestamp(item.created),
            renderTargetSummary(item.targetApps),
            html`<ak-status-label
                .good=${item.isActive}
                good-label=${statusLabel(item.status)}
                bad-label=${statusLabel(item.status)}
                type="info"
            ></ak-status-label>`,
            this.renderActions(item),
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-access-requests-list": AccessRequestListPage;
    }
}
