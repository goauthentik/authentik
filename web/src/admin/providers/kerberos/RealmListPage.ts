import "@goauthentik/admin/providers/ProviderWizard";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/forms/ProxyForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { KerberosRealm, KerberosApi } from "@goauthentik/api";

@customElement("ak-kerberos-realm-list")
export class KerberosRealmListPage extends TablePage<KerberosRealm> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Kerberos Realms");
    }
    pageDescription(): string {
        return msg("List of Kerberos realms you can attach your Kerberos providers to.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-cloud-security";
    }

    checkbox = true;

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<PaginatedResponse<KerberosRealm>> {
        return new KerberosApi(DEFAULT_CONFIG).kerberosRealmsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Realm(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: KerberosRealm) => {
                return new KerberosApi(DEFAULT_CONFIG).kerberosRealmsUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: KerberosRealm) => {
                return new KerberosApi(DEFAULT_CONFIG).kerberosRealmsDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: KerberosReaom): TemplateResult[] {
        return [
            html`<a href="#/kerberos/realms/${item.pk}"> ${item.name} </a>`,
            html`<ak-forms-modal>
                <span slot="submit"> ${msg("Update")} </span>
                <span slot="header"> ${msg(str`Update ${item.name}`)} </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        instancePk: item.pk,
                    }}
                    type=ak-kerberos-realm-form
                >
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${msg("Create")} </span>
                <span slot="header"> ${msg("Create Kerberos Realm")} </span>
                <ak-kerberos-realm-form slot="form"> </ak-kerberos-realm-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-forms-modal>
        `;
    }
}
