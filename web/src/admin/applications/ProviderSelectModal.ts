import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TableModal } from "#elements/table/TableModal";

import { Provider, ProvidersApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-select-table")
export class ProviderSelectModal extends TableModal<Provider> {
    public override checkbox = true;
    public override checkboxChip = true;

    protected override searchEnabled(): boolean {
        return true;
    }

    @property({ type: Boolean })
    public backchannel = false;

    @property()
    public confirm!: (selectedItems: Provider[]) => Promise<unknown>;

    public override order = "name";

    protected async apiEndpoint(): Promise<PaginatedResponse<Provider>> {
        return new ProvidersApi(DEFAULT_CONFIG).providersAllList({
            ...(await this.defaultEndpointConfig()),
            backchannel: this.backchannel,
        });
    }

    protected columns(): TableColumn[] {
        return [new TableColumn(msg("Name"), "username"), new TableColumn(msg("Type"))];
    }

    protected row(item: Provider): TemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
            </div>`,
            html`${item.verboseName}`,
        ];
    }

    protected override renderSelectedChip(item: Provider): TemplateResult {
        return html`${item.name}`;
    }

    protected override renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">
                        ${msg("Select providers to add to application")}
                    </h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">${this.renderTable()}</section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${async () => {
                        await this.confirm(this.selectedElements);
                        this.open = false;
                    }}
                    class="pf-m-primary"
                >
                    ${msg("Add")} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-select-table": ProviderSelectModal;
    }
}
