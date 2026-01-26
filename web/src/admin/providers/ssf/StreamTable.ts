import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { SsfApi, SSFStream } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-ssf-stream-list")
export class SSFProviderStreamList extends Table<SSFStream> {
    protected override searchEnabled = true;
    checkbox = true;
    clearOnRefresh = true;

    @property({ type: Number })
    providerId?: number;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<SSFStream>> {
        return new SsfApi(DEFAULT_CONFIG).ssfStreamsList({
            provider: this.providerId,
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected override rowLabel(item: SSFStream): string | null {
        return item.aud?.join(", ") ?? null;
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Audience"), "aud"],
    ];

    row(item: SSFStream): SlottedTemplateResult[] {
        return [html`${item.aud}`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ssf-stream-list": SSFProviderStreamList;
    }
}
