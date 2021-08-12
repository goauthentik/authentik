import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Table, TableColumn } from "../table/Table";

import "../forms/DeleteBulkForm";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, AuthenticatedSession } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-user-session-list")
export class AuthenticatedSessionList extends Table<AuthenticatedSession> {
    @property()
    targetUser!: string;

    apiEndpoint(page: number): Promise<AKResponse<AuthenticatedSession>> {
        return new CoreApi(DEFAULT_CONFIG).coreAuthenticatedSessionsList({
            userUsername: this.targetUser,
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
        });
    }

    checkbox = true;
    order = "-expires";

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Last IP`, "last_ip"),
            new TableColumn(t`Browser`, "user_agent"),
            new TableColumn(t`Device`, "user_agent"),
            new TableColumn(t`Expires`, "expires"),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Session(s)`}
            .objects=${this.selectedElements}
            .usedBy=${(item: AuthenticatedSession) => {
                return new CoreApi(DEFAULT_CONFIG).coreAuthenticatedSessionsUsedByList({
                    uuid: item.uuid || "",
                });
            }}
            .delete=${(item: AuthenticatedSession) => {
                return new CoreApi(DEFAULT_CONFIG).coreAuthenticatedSessionsDestroy({
                    uuid: item.uuid || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: AuthenticatedSession): TemplateResult[] {
        return [
            html`${item.lastIp}`,
            html`${item.userAgent.userAgent?.family}`,
            html`${item.userAgent.os?.family}`,
            html`${item.expires?.toLocaleString()}`,
        ];
    }
}
