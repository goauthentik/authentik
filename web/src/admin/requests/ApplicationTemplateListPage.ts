import "#admin/rbac/ObjectPermissionModal";
import "#admin/requests/ApplicationTemplateForm";
import "#admin/requests/BoundRequestRulesTable";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import { aki } from "#common/api/client";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { ApplicationTemplateForm } from "#admin/requests/ApplicationTemplateForm";

import { ApplicationTemplate, ModelEnum, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-application-template-list")
export class ApplicationTemplateListPage extends TablePage<ApplicationTemplate> {
    public override checkbox = true;
    public override clearOnRefresh = true;
    public override expandable = true;
    public override searchPlaceholder = msg("Search for an application template by name...", {
        id: "requests.application-template.list.search-placeholder",
    });
    public override pageTitle = msg("Application Templates", {
        id: "requests.application-template.verbose-name-plural",
    });
    public override pageDescription = msg(
        "Let users request new applications. A template sets what the created provider uses; the request rules bound to it decide who may request and who approves.",
        { id: "requests.application-template.list.description" },
    );
    public override pageIcon = "pf-icon pf-icon-applications";

    public override order = "name";

    protected override searchEnabled = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<ApplicationTemplate>> {
        return aki(RequestsApi).requestsApplicationTemplatesList(
            await this.defaultEndpointConfig(),
        );
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Bindable groups", { id: "requests.application-template.bindable-groups.label" })],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Application template(s)", {
                id: "requests.application-template.list.delete-label",
            })}
            .objects=${this.selectedElements}
            .usedBy=${(item: ApplicationTemplate) => {
                return aki(RequestsApi).requestsApplicationTemplatesUsedByList({
                    uuid: item.uuid ?? "",
                });
            }}
            .delete=${(item: ApplicationTemplate) => {
                return aki(RequestsApi).requestsApplicationTemplatesDestroy({
                    uuid: item.uuid ?? "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: ApplicationTemplate): SlottedTemplateResult[] {
        return [
            item.name,
            item.bindableGroupsObj.map((group) => group.name).join(", "),
            html`<div class="ak-c-table__actions">
                ${IconEditButton(ApplicationTemplateForm, item.uuid ?? "", item.name)}
                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikRequestsApplicationtemplate}
                    objectPk=${item.uuid ?? ""}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderExpanded(item: ApplicationTemplate): SlottedTemplateResult {
        return html`<ak-bound-request-rules-table
            .target=${item.pbmUuid}
            .entitlements=${false}
        ></ak-bound-request-rules-table>`;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(ApplicationTemplateForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-template-list": ApplicationTemplateListPage;
    }
}
