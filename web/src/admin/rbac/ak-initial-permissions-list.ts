import "#admin/rbac/ak-initial-permissions-form";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { setPageDetails } from "#components/ak-page-navbar";

import { InitialPermissionsForm } from "#admin/rbac/ak-initial-permissions-form";

import { InitialPermissions, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-initial-permissions-list")
export class InitialPermissionsListPage extends TablePage<InitialPermissions> {
    protected override searchEnabled = true;

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for initial permissions by name...");
    protected override emptyStateMessage = msg("Create an initial permission to get started.");

    public override pageTitle = msg("Initial Permissions");
    public override pageDescription = msg("Set initial permissions for newly created objects.");
    public override pageIcon = "fa fa-lock";

    public override order = "name";

    protected override async apiEndpoint(): Promise<PaginatedResponse<InitialPermissions>> {
        return new RbacApi(DEFAULT_CONFIG).rbacInitialPermissionsList(
            await this.defaultEndpointConfig(),
        );
    }

    protected override columns: TableColumn[] = [
        // ---
        [msg("Name"), "name"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Initial Permissions")}
            .objects=${this.selectedElements}
            .usedBy=${(item: InitialPermissions) => {
                return new RbacApi(DEFAULT_CONFIG).rbacInitialPermissionsUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: InitialPermissions) => {
                return new RbacApi(DEFAULT_CONFIG).rbacInitialPermissionsDestroy({
                    id: item.pk,
                });
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

    protected override row(item: InitialPermissions): SlottedTemplateResult[] {
        return [
            item.name,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(InitialPermissionsForm, item.pk)}
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(InitialPermissionsForm);
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
        "ak-initial-permissions-list": InitialPermissionsListPage;
    }
}
