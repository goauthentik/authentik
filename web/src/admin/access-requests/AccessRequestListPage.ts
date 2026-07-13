import "../../components/ak-status-label";

import { aki } from "#common/api/client";
import { PaginatedResponse } from "#common/api/responses";

import { modalInvoker } from "#elements/dialogs";
import { RowType, Timestamp } from "#elements/table/Table";
import { TableColumn } from "#elements/table/TableColumn";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { AccessRequestFulfillForm } from "#admin/access-requests/AccessRequestFulfillForm";

import { GrantRequest, PamApi, RequestStatus } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit-html";
import { customElement } from "lit/decorators.js";

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

    renderApps(item: GrantRequest): SlottedTemplateResult {
        if (item.targetApps.length < 1) {
            return nothing;
        }
        const overflow = item.targetApps.length - 1;
        const base = html`<a href="">${item.targetApps[0].name}</a> ${overflow > 0
                ? `+${overflow}`
                : ""}`;
        return base;
    }

    protected row(item: GrantRequest): RowType[] {
        return [
            html`<a href="#/identity/users/${item.createdBy.pk}">
                <div>${item.createdBy.username}</div>
                <small>${item.createdBy.name}</small>
            </a>`,
            Timestamp(item.created),
            this.renderApps(item),
            html`<ak-status-label
                .good=${item.status === RequestStatus.Approved}
                good-label=${msg("Approved")}
                bad-label=${msg("Pending")}
                type="info"
            ></ak-status-label>`,
            html`<button
                class="pf-c-button pf-m-secondary pf-m-block"
                ${modalInvoker(AccessRequestFulfillForm, {
                    request: item,
                })}
            >
                ${msg("Fulfill")}
            </button>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-access-requests-list": AccessRequestListPage;
    }
}
