import "#admin/locale-catalogs/LocaleCatalogForm";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { LocaleCatalogForm } from "#admin/locale-catalogs/LocaleCatalogForm";

import { AdminApi, LocaleCatalog, ModelEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-locale-catalog-list")
export class LocaleCatalogListPage extends TablePage<LocaleCatalog> {
    protected override searchEnabled = true;
    public override searchPlaceholder = msg("Search by name or locale...", {
        id: "locale-catalog.list.search.placeholder",
    });
    public pageTitle = msg("Locale Catalogs", { id: "locale-catalog.list.title" });
    public pageDescription = msg(
        "Customize and add translations of the interface and messages sent by authentik.",
        { id: "locale-catalog.list.description" },
    );
    public pageIcon = "pf-icon pf-icon-globe-route";

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "locale";

    async apiEndpoint(): Promise<PaginatedResponse<LocaleCatalog>> {
        return aki(AdminApi).adminLocaleCatalogsList(await this.defaultEndpointConfig());
    }

    protected override rowLabel(item: LocaleCatalog): string | null {
        return item.name;
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Locale", { id: "locale-catalog.list.column.locale" }), "locale"],
        [msg("Order"), "order"],
        [msg("Messages", { id: "locale-catalog.list.column.messages" })],
        [msg("Enabled"), "enabled"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Locale catalog(s)", { id: "locale-catalog.list.object-label" })}
            .objects=${this.selectedElements}
            .metadata=${(item: LocaleCatalog) => {
                return [
                    { key: msg("Name"), value: item.name },
                    {
                        key: msg("Locale", { id: "locale-catalog.list.column.locale" }),
                        value: item.locale,
                    },
                ];
            }}
            .usedBy=${(item: LocaleCatalog) => {
                return aki(AdminApi).adminLocaleCatalogsUsedByList({
                    catalogUuid: item.catalogUuid,
                });
            }}
            .delete=${(item: LocaleCatalog) => {
                return aki(AdminApi).adminLocaleCatalogsDestroy({
                    catalogUuid: item.catalogUuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: LocaleCatalog): SlottedTemplateResult[] {
        const count = Object.keys(item.messages ?? {}).length;

        return [
            item.name,
            html`<code>${item.locale}</code>`,
            String(item.order ?? 0),
            msg(str`${count} message(s)`, { id: "locale-catalog.list.message-count" }),
            html`<ak-status-label ?good=${item.enabled}></ak-status-label>`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(LocaleCatalogForm, item.catalogUuid, item.name)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikAdminI18nLocalecatalog}
                    objectPk=${item.catalogUuid}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(LocaleCatalogForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-locale-catalog-list": LocaleCatalogListPage;
    }
}
