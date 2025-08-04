import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/forms/ProxyForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";

import { SsfApi, SSFStream } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-ssf-stream-list")
export class SSFProviderStreamList extends Table<SSFStream> {
    protected override searchEnabled(): boolean {
        return true;
    }
    public override checkbox = true;
    public override clearOnRefresh = true;

    @property({ type: Number })
    public providerId?: number;

    @property()
    public override order = "name";

    protected async apiEndpoint(): Promise<PaginatedResponse<SSFStream>> {
        return new SsfApi(DEFAULT_CONFIG).ssfStreamsList({
            provider: this.providerId,
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected columns(): TableColumn[] {
        return [new TableColumn(msg("Audience"), "aud")];
    }

    protected row(item: SSFStream): TemplateResult[] {
        return [html`${item.aud}`];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-ssf-stream-list": SSFProviderStreamList;
    }
}
