import { DEFAULT_CONFIG } from "#common/api/config";
import { PaginatedResponse } from "#common/api/responses";

import { RowType } from "#elements/table/Table";
import { TableColumn } from "#elements/table/TableColumn";
import { TablePage } from "#elements/table/TablePage";

import { GrantRequest, PamApi } from "#packages/client-ts/dist";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement } from "lit/decorators.js";

@customElement("ak-access-requests-list")
export class AccessRequestListPage extends TablePage<GrantRequest> {
    public pageTitle: string = msg("Access Requests");
    public pageDescription: string = msg("");
    public pageIcon: string = "";
    protected async apiEndpoint(): Promise<PaginatedResponse<GrantRequest, object>> {
        return new PamApi(DEFAULT_CONFIG).pamGrantRequestsList({
            ...(await this.defaultEndpointConfig()),
        });
    }
    protected columns: TableColumn[] = [[""]];
    protected row(item: GrantRequest): RowType[] {
        return [html``];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-access-requests-list": AccessRequestListPage;
    }
}
