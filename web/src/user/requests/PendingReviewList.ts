import "#elements/EmptyState";
import "#elements/forms/ModalForm";
import "#user/requests/AccessRequestFulfillForm";

import { aki } from "#common/api/client";
import { PaginatedResponse } from "#common/api/responses";

import { modalInvoker } from "#elements/dialogs";
import { RowType, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { AccessRequestFulfillForm } from "#user/requests/AccessRequestFulfillForm";
import { renderTargetSummary } from "#user/requests/RequestableTargetHelpers";

import { GrantRequest, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-pending-review-list")
export class PendingReviewList extends Table<GrantRequest> {
    protected override async apiEndpoint(): Promise<PaginatedResponse<GrantRequest>> {
        return aki(RequestsApi).requestsGrantRequestsPendingReviewList({
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected override columns: TableColumn[] = [
        [msg("Requester")],
        [msg("Apps")],
        [msg("Requested")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override row(item: GrantRequest): RowType[] {
        return [
            html`<div>${item.createdBy.username}</div>
                <small>${item.createdBy.name}</small>`,
            renderTargetSummary(item.targetObjs ?? []),
            Timestamp(item.created),
            html`<button
                class="pf-c-button pf-m-secondary pf-m-block"
                ${modalInvoker(AccessRequestFulfillForm, {
                    request: item,
                })}
            >
                ${msg("Review")}
            </button>`,
        ];
    }

    protected override renderEmpty(): SlottedTemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon="pf-icon-catalog"
                ><span>${msg("Nothing to review.")}</span>
                <div slot="body">
                    ${msg("Requests waiting on your approval will show up here.")}
                </div>
            </ak-empty-state>`,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-pending-review-list": PendingReviewList;
    }
}
