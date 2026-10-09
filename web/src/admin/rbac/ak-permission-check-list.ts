import "#admin/rbac/ak-permission-check-form";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/Label";
import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PFColor } from "#elements/Label";
import { setPageDetails } from "#elements/router/meta";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { PermissionCheckForm } from "#admin/rbac/ak-permission-check-form";

import { PermissionCheck, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { PropertyValues, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-permission-check-list")
export class PermissionCheckListPage extends TablePage<PermissionCheck> {
    protected override searchEnabled = true;

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg("Search for permission checks...");
    protected override emptyStateMessage = msg("Create a permission check to get started.");

    public override pageTitle = msg("Permission Checks");
    public override pageDescription = msg(
        "Python code that has the final say on access to API endpoints.",
    );
    public override pageIcon = "fa fa-code";

    public override order = "name";

    protected override async apiEndpoint(): Promise<PaginatedResponse<PermissionCheck>> {
        return aki(RbacApi).rbacPermissionChecksList(await this.defaultEndpointConfig());
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Bound to")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Permission Checks")}
            .objects=${this.selectedElements}
            .usedBy=${(item: PermissionCheck) => {
                return aki(RbacApi).rbacPermissionChecksUsedByList({ checkUuid: item.pk });
            }}
            .delete=${(item: PermissionCheck) => {
                return aki(RbacApi).rbacPermissionChecksDestroy({ checkUuid: item.pk });
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

    protected override row(item: PermissionCheck): SlottedTemplateResult[] {
        return [
            item.name,
            html`${(item.endpoints ?? []).map(
                (endpoint) =>
                    html`<code>${endpoint}</code> ${
                            item.unknownEndpoints.includes(endpoint)
                                ? html`<ak-label color=${PFColor.Orange} compact>
                                      ${msg("No longer exists")}
                                  </ak-label>`
                                : nothing
                        }<br />`,
            )}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(PermissionCheckForm, item.pk)}
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(PermissionCheckForm);
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
        "ak-permission-check-list": PermissionCheckListPage;
    }
}
