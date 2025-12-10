import "#elements/forms/DeleteBulkForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { AuthenticatedSession, CoreApi } from "@goauthentik/api";

import getUnicodeFlagIcon from "country-flag-icons/unicode";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-session-list")
export class AuthenticatedSessionList extends Table<AuthenticatedSession> {
    @property()
    targetUser!: string;

    async apiEndpoint(): Promise<PaginatedResponse<AuthenticatedSession>> {
        return new CoreApi(DEFAULT_CONFIG).coreAuthenticatedSessionsList({
            ...(await this.defaultEndpointConfig()),
            userUsername: this.targetUser,
        });
    }

    checkbox = true;
    clearOnRefresh = true;
    order = "-expires";

    protected override rowLabel(item: AuthenticatedSession): string | null {
        return item.lastIp ?? null;
    }

    protected columns: TableColumn[] = [
        [msg("Last IP"), "last_ip"],
        [msg("Last used"), "last_used"],
        [msg("Expires"), "expires"],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Session(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: AuthenticatedSession) => {
                return [
                    { key: msg("Last IP"), value: item.lastIp },
                    { key: msg("Expiry"), value: item.expires?.toLocaleString() || msg("-") },
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
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: AuthenticatedSession): SlottedTemplateResult[] {
        return [
            html`<div>
                    ${item.geoIp?.country
                        ? html`${getUnicodeFlagIcon(item.geoIp.country)}&nbsp;`
                        : nothing}
                    ${item.current ? html`${msg("(Current session)")}&nbsp;` : nothing}
                    ${item.lastIp}
                </div>
                <small>${item.userAgent.userAgent?.family}, ${item.userAgent.os?.family}</small>`,
            Timestamp(item.lastUsed),
            Timestamp(item.expires ?? new Date()),
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-session-list": AuthenticatedSessionList;
    }
}
