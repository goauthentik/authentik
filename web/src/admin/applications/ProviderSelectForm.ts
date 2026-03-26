import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Provider, ProvidersApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-select-form")
export class ProviderSelectForm extends Table<Provider> {
    public override checkbox = true;
    public override checkboxChip = true;

    protected override searchEnabled = true;

    @property({ type: Boolean })
    public backchannel = false;

    public override order = "name";

    protected async apiEndpoint(): Promise<PaginatedResponse<Provider>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersAllList({
            ...(await this.defaultEndpointConfig()),
            backchannel: this.backchannel,
        });
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name"), "username"],
        [msg("Type")],
    ];

    protected row(item: Provider): SlottedTemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
            </div>`,
            html`${item.verboseName}`,
        ];
    }

    protected renderSelectedChip(item: Provider): SlottedTemplateResult {
        return item.name;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-select-form": ProviderSelectForm;
    }
}
