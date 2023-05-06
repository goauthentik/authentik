import "@goauthentik/admin/interfaces/InterfaceForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Interface, InterfacesApi } from "@goauthentik/api";

@customElement("ak-interface-list")
export class InterfaceListPage extends TablePage<Interface> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Interfaces`;
    }
    pageDescription(): string {
        return t`Manage custom interfaces for authentik`;
    }
    pageIcon(): string {
        return "fa fa-home";
    }

    checkbox = true;

    @property()
    order = "url_name";

    async apiEndpoint(page: number): Promise<PaginatedResponse<Interface>> {
        return new InterfacesApi(DEFAULT_CONFIG).interfacesList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(t`URL Name`, "url_name"), new TableColumn(t`Actions`)];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Interface(s)`}
            .objects=${this.selectedElements}
            .metadata=${(item: Interface) => {
                return [{ key: t`Domain`, value: item.urlName }];
            }}
            .usedBy=${(item: Interface) => {
                return new InterfacesApi(DEFAULT_CONFIG).interfacesUsedByList({
                    interfaceUuid: item.interfaceUuid,
                });
            }}
            .delete=${(item: Interface) => {
                return new InterfacesApi(DEFAULT_CONFIG).interfacesDestroy({
                    interfaceUuid: item.interfaceUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Interface): TemplateResult[] {
        return [
            html`${item.urlName}`,
            html`<ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update Interface`} </span>
                <ak-interface-form slot="form" .instancePk=${item.interfaceUuid}>
                </ak-interface-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Interface`} </span>
                <ak-interface-form slot="form"> </ak-interface-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
        `;
    }
}
