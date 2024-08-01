import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/DeleteBulkForm";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { ProvidersApi, SCIMProviderGroup } from "@goauthentik/api";

@customElement("ak-provider-scim-groups-list")
export class SCIMProviderGroupList extends Table<SCIMProviderGroup> {
    @property({ type: Number })
    providerId?: number;

    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;
    clearOnRefresh = true;

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("SCIM Group(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: SCIMProviderGroup) => {
                return new ProvidersApi(DEFAULT_CONFIG).providersScimGroupsDestroy({
                    id: item.id,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    async apiEndpoint(): Promise<PaginatedResponse<SCIMProviderGroup>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersScimGroupsList({
            ...(await this.defaultEndpointConfig()),
            providerId: this.providerId,
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Name")), new TableColumn(msg("ID"))];
    }

    row(item: SCIMProviderGroup): TemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.groupObj.pk}">
                <div>${item.groupObj.name}</div>
            </a>`,
            html`${item.id}`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-scim-groups-list": SCIMProviderGroupList;
    }
}
