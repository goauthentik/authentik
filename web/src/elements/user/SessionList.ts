import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { AuthenticatedSession, CoreApi } from "@goauthentik/api";

@customElement("ak-user-session-list")
export class AuthenticatedSessionList extends Table<AuthenticatedSession> {
    @property()
    targetUser!: string;

    async apiEndpoint(page: number): Promise<PaginatedResponse<AuthenticatedSession>> {
        return new CoreApi(DEFAULT_CONFIG).coreAuthenticatedSessionsList({
            userUsername: this.targetUser,
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
        });
    }

    checkbox = true;
    order = "-expires";

    columns(): TableColumn[] {
        return [new TableColumn(t`Last IP`, "last_ip"), new TableColumn(t`Expires`, "expires")];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Session(s)`}
            .objects=${this.selectedElements}
            .metadata=${(item: AuthenticatedSession) => {
                return [
                    { key: t`Last IP`, value: item.lastIp },
                    { key: t`Expiry`, value: item.expires?.toLocaleString() || t`-` },
                ];
            }}
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
            html`<div>
                    ${item.current ? html`${t`(Current session)`}&nbsp;` : html``}${item.lastIp}
                </div>
                <small>${item.userAgent.userAgent?.family}, ${item.userAgent.os?.family}</small>`,
            html`${item.expires?.toLocaleString()}`,
        ];
    }
}
