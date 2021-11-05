import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, UserConsent } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { uiConfig } from "../../common/config";
import "../forms/DeleteBulkForm";
import { Table, TableColumn } from "../table/Table";

@customElement("ak-user-consent-list")
export class UserConsentList extends Table<UserConsent> {
    @property({ type: Number })
    userId?: number;

    async apiEndpoint(page: number): Promise<AKResponse<UserConsent>> {
        return new CoreApi(DEFAULT_CONFIG).coreUserConsentList({
            user: this.userId,
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
        });
    }

    checkbox = true;
    order = "-expires";

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Application`, "application"),
            new TableColumn(t`Expires`, "expires"),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Consent(s)`}
            .objects=${this.selectedElements}
            .usedBy=${(item: UserConsent) => {
                return new CoreApi(DEFAULT_CONFIG).coreUserConsentUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: UserConsent) => {
                return new CoreApi(DEFAULT_CONFIG).coreUserConsentDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: UserConsent): TemplateResult[] {
        return [html`${item.application.name}`, html`${item.expires?.toLocaleString()}`];
    }
}
