import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { MicrosoftEntraProviderGroup, ProvidersApi } from "@goauthentik/api";

@customElement("ak-provider-microsoft-entra-groups-list")
export class MicrosoftEntraProviderGroupList extends Table<MicrosoftEntraProviderGroup> {
    @property({ type: Number })
    providerId?: number;

    searchEnabled(): boolean {
        return true;
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<MicrosoftEntraProviderGroup>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersMicrosoftEntraGroupsList({
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            ordering: this.order,
            search: this.search || "",
            providerId: this.providerId,
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(msg("Name")), new TableColumn(msg("ID"))];
    }

    row(item: MicrosoftEntraProviderGroup): TemplateResult[] {
        return [
            html`<a href="#/identity/groups/${item.groupObj.pk}">
                <div>${item.groupObj.name}</div>
            </a>`,
            html`${item.id}`,
        ];
    }
}
