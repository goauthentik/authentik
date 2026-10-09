import "#admin/locale-catalogs/BrandLocaleCatalogForm";
import "#elements/forms/DeleteBulkForm";
import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { BrandLocaleCatalogForm } from "#admin/locale-catalogs/BrandLocaleCatalogForm";

import { AdminApi, BrandLocaleCatalog, ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * The locale catalogs bound to a brand.
 */
@customElement("ak-bound-locale-catalogs-list")
export class BoundLocaleCatalogsList extends Table<BrandLocaleCatalog> {
    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "order";

    @property({ type: String })
    public brand: string | null = null;

    protected override async apiEndpoint(): Promise<PaginatedResponse<BrandLocaleCatalog>> {
        return aki(AdminApi).adminLocaleCatalogBindingsList({
            ...(await this.defaultEndpointConfig()),
            brand: this.brand ?? "",
        });
    }

    protected override rowLabel(item: BrandLocaleCatalog): string {
        return `#${item.order} ${item.catalogObj.name}`;
    }

    protected columns: TableColumn[] = [
        [msg("Order"), "order"],
        [msg("Name"), "catalog__name"],
        [msg("Locale", { id: "locale-catalog.list.column.locale" }), "catalog__locale"],
        [msg("Enabled")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Locale catalog binding(s)", {
                id: "locale-catalog.binding.list.object-label",
            })}
            .objects=${this.selectedElements}
            .metadata=${(item: BrandLocaleCatalog) => [
                { key: msg("Name"), value: item.catalogObj.name },
                {
                    key: msg("Locale", { id: "locale-catalog.list.column.locale" }),
                    value: item.catalogObj.locale,
                },
            ]}
            .usedBy=${(item: BrandLocaleCatalog) =>
                aki(AdminApi).adminLocaleCatalogBindingsUsedByList({
                    bindingUuid: item.bindingUuid,
                })}
            .delete=${(item: BrandLocaleCatalog) =>
                aki(AdminApi).adminLocaleCatalogBindingsDestroy({
                    bindingUuid: item.bindingUuid,
                })}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: BrandLocaleCatalog): SlottedTemplateResult[] {
        return [
            html`<pre>${item.order}</pre>`,
            item.catalogObj.name,
            html`<code>${item.catalogObj.locale}</code>`,
            html`<ak-status-label ?good=${item.catalogObj.enabled}></ak-status-label>`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(BrandLocaleCatalogForm, item.bindingUuid, item.catalogObj.name)}
                ${IconPermissionButton(item.catalogObj.name, {
                    model: ModelEnum.AuthentikAdminI18nBrandlocalecatalog,
                    objectPk: item.bindingUuid,
                })}
            </div>`,
        ];
    }

    protected override renderToolbar(): SlottedTemplateResult {
        return [
            ModalInvokerButton(BrandLocaleCatalogForm, { brandPk: this.brand ?? undefined }),
            super.renderToolbar(),
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-bound-locale-catalogs-list": BoundLocaleCatalogsList;
    }
}
