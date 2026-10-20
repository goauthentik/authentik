import "#admin/rbac/ak-custom-permission-form";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { setPageDetails } from "#elements/router/meta";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { CustomPermissionForm } from "#admin/rbac/ak-custom-permission-form";

import { CustomPermission, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-custom-permission-list")
export class CustomPermissionListPage extends TablePage<CustomPermission> {
    protected override searchEnabled = true;

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for custom permissions...");
    protected override emptyStateMessage = msg("Create a custom permission to get started.");

    public override pageTitle = msg("Custom Permissions");
    public override pageDescription = msg(
        "Define your own permissions on models, assign them to roles, and test them in permission checks.",
    );
    public override pageIcon = "fa fa-key";

    public override order = "codename";

    protected override async apiEndpoint(): Promise<PaginatedResponse<CustomPermission>> {
        return aki(RbacApi).rbacCustomPermissionsList(await this.defaultEndpointConfig());
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Permission"), "codename"],
        [msg("Model")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Custom Permissions")}
            .objects=${this.selectedElements}
            .delete=${(item: CustomPermission) => {
                return aki(RbacApi).rbacCustomPermissionsDestroy({ id: item.pk });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override render(): SlottedTemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-no-padding-mobile">
            <div class="pf-c-card">${this.renderTable()}</div>
        </section>`;
    }

    protected override row(item: CustomPermission): SlottedTemplateResult[] {
        return [
            item.name,
            html`<code>${item.permission}</code>`,
            item.model,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(CustomPermissionForm, item.pk)}
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(CustomPermissionForm);
    }

    public override updated(changed: PropertyValues<this>) {
        super.updated(changed);

        setPageDetails({
            icon: this.pageIcon,
            header: this.pageTitle,
            description: this.pageDescription,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-custom-permission-list": CustomPermissionListPage;
    }
}
