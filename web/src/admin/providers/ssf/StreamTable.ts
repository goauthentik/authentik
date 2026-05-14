import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList from "#components/DescriptionList";

import { SSFDeliveryMethodToLabel } from "#admin/providers/ssf/utils";

import { SsfApi, SSFStream } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-provider-ssf-stream-list")
export class SSFProviderStreamList extends Table<SSFStream> {
    protected override searchEnabled = true;
    public checkbox: boolean = true;
    public clearOnRefresh: boolean = true;
    public expandable: boolean = true;

    @property({ type: Number })
    providerId?: number;

    @property()
    order = "name";

    static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    async apiEndpoint(): Promise<PaginatedResponse<SSFStream>> {
        return new SsfApi(DEFAULT_CONFIG).ssfStreamsList({
            provider: this.providerId,
            ...(await this.defaultEndpointConfig()),
            pageSize: 10,
        });
    }

    protected override renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Stream(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: SSFStream) => {
                return new SsfApi(DEFAULT_CONFIG).ssfStreamsDestroy({
                    uuid: item.pk,
                });
            }}
            .metadata=${(item: SSFStream) => {
                return [
                    { key: msg("Audience"), value: item.aud },
                    {
                        key: msg("Delivery method"),
                        value: SSFDeliveryMethodToLabel(item.deliveryMethod),
                    },
                    { key: msg("Endpoint"), value: item.endpointUrl ?? "-" },
                ];
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override rowLabel(item: SSFStream): string | null {
        return item.aud?.join(", ") ?? null;
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Audience"), "aud"],
        [msg("Delivery Method"), "delivery_method"],
    ];

    protected renderExpanded(item: SSFStream): SlottedTemplateResult {
        return html`${renderDescriptionList([
            [msg("Delivery method"), html`${SSFDeliveryMethodToLabel(item.deliveryMethod)}`],
            [msg("Endpoint"), html`${item.endpointUrl ?? "-"}`],
        ])}`;
    }

    row(item: SSFStream): SlottedTemplateResult[] {
        return [html`${item.aud}`, html`${SSFDeliveryMethodToLabel(item.deliveryMethod)}`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ssf-stream-list": SSFProviderStreamList;
    }
}
