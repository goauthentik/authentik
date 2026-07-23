import "#components/ak-status-label";
import "#elements/EmptyState";
import "#elements/forms/ConfirmationForm";

import { aki } from "#common/api/client";
import { PaginatedResponse } from "#common/api/responses";

import { WithSession } from "#elements/mixins/session";
import { RowType, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { renderTargetSummary } from "#user/requests/RequestableTargetHelpers";

import { GrantRequest, RequestsApi, RequestStatus } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
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

@customElement("ak-my-grant-requests-list")
export class MyGrantRequestsList extends WithSession(Table<GrantRequest>) {
    protected override async apiEndpoint(): Promise<PaginatedResponse<GrantRequest>> {
        return aki(RequestsApi).requestsGrantRequestsList({
            ...(await this.defaultEndpointConfig()),
            createdBy: this.currentUser?.pk,
        });
    }

    protected override columns: TableColumn[] = [
        [msg("Apps")],
        [msg("Requested")],
        [msg("Status")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected renderActions(item: GrantRequest): SlottedTemplateResult {
        if (item.status !== RequestStatus.Created) {
            return nothing;
        }
        return html`<ak-forms-confirm
            successMessage=${msg("Successfully cancelled request")}
            errorMessage=${msg("Failed to cancel request")}
            action=${msg("Cancel")}
            .onConfirm=${() => {
                return aki(RequestsApi).requestsGrantRequestsDestroy({
                    uuid: item.uuid || "",
                });
            }}
        >
            <span slot="header">${msg("Cancel request")}</span>
            <p slot="body">${msg("Are you sure you want to cancel this pending request?")}</p>
            <button slot="trigger" class="pf-c-button pf-m-danger" type="button">
                ${msg("Cancel")}
            </button>
        </ak-forms-confirm>`;
    }

    protected override row(item: GrantRequest): RowType[] {
        return [
            renderTargetSummary(item.targetObjs ?? []),
            Timestamp(item.created),
            html`<ak-status-label
                .good=${item.isActive}
                good-label=${statusLabel(item.status)}
                bad-label=${statusLabel(item.status)}
                type="info"
            ></ak-status-label>`,
            this.renderActions(item),
        ];
    }

    protected override renderEmpty(): SlottedTemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon="pf-icon-catalog"
                ><span>${msg("No requests yet.")}</span>
                <div slot="body">${msg("Requests you've made for access will show up here.")}</div>
            </ak-empty-state>`,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-my-grant-requests-list": MyGrantRequestsList;
    }
}
