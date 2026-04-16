import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Provider, ProvidersApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-table")
export class ProviderTable extends Table<Provider> {
    public override checkbox = true;
    public override checkboxChip = true;

    protected override searchEnabled = true;

    @property({ type: Boolean })
    public backchannel = false;

    public override order = "name";

    protected override async apiEndpoint(): Promise<PaginatedResponse<Provider>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersAllList({
            ...(await this.defaultEndpointConfig()),
            backchannel: this.backchannel,
        });
    }

    protected override columns: TableColumn[] = [
        // ---
        [msg("Name"), "username"],
        [msg("Type")],
    ];

    protected override row(item: Provider): SlottedTemplateResult[] {
        return [item.name, item.verboseName];
    }

    protected override renderSelectedChip(item: Provider): SlottedTemplateResult {
        return item.name;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-table": ProviderTable;
    }
}
