import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Table, TableColumn } from "../table/Table";

import "../forms/DeleteForm";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, UserConsent } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-user-consent-list")
export class UserConsentList extends Table<UserConsent> {
    @property({ type: Number })
    userId?: number;

    apiEndpoint(page: number): Promise<AKResponse<UserConsent>> {
        return new CoreApi(DEFAULT_CONFIG).coreUserConsentList({
            user: this.userId,
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
        });
    }

    order = "-expires";

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Application`, "application"),
            new TableColumn(t`Expires`, "expires"),
            new TableColumn(""),
        ];
    }

    row(item: UserConsent): TemplateResult[] {
        return [
            html`${item.application.name}`,
            html`${item.expires?.toLocaleString()}`,
            html`
            <ak-forms-delete
                .obj=${item}
                objectLabel=${t`Consent`}
                .usedBy=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreUserConsentUsedByList({
                        id: item.pk
                    });
                }}
                .delete=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreUserConsentDestroy({
                        id: item.pk,
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${t`Delete Consent`}
                </button>
            </ak-forms-delete>`,
        ];
    }

}
