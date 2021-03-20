import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { Table, TableColumn } from "../table/Table";

import "../forms/DeleteForm";
import { PAGE_SIZE } from "../../constants";
import { CoreApi, UserConsent } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

@customElement("ak-user-consent-list")
export class UserConsentList extends Table<UserConsent> {
    @property()
    userId?: string;

    apiEndpoint(page: number): Promise<AKResponse<UserConsent>> {
        return new CoreApi(DEFAULT_CONFIG).coreUserConsentList({
            user: this.userId,
            ordering: "expires",
            page: page,
            pageSize: PAGE_SIZE,
        });
    }

    order = "-expires";

    columns(): TableColumn[] {
        return [
            new TableColumn("Application", "application"),
            new TableColumn("Expires", "expires"),
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
                objectLabel=${gettext("Consent")}
                .delete=${() => {
                    return new CoreApi(DEFAULT_CONFIG).coreUserConsentDelete({
                        id: item.pk || 0,
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete Consent")}
                </button>
            </ak-forms-delete>`,
        ];
    }

}
