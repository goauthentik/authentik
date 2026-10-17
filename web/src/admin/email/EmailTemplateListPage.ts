/**
 * @file Display the table of email templates
 */

import "#admin/rbac/ObjectPermissionModal";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import { aki } from "#common/api/client";
import { groupBy, GroupResult } from "#common/utils";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { EmailTemplateForm } from "#admin/email/EmailTemplateForm";

import { EmailTemplate, ModelEnum, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-email-template-list")
export class EmailTemplateListPage extends TablePage<EmailTemplate> {
    protected override searchEnabled = true;
    public pageTitle = msg("Email Templates");
    public pageDescription = msg("Templates used by email stages and notification transports.");
    public pageIcon = "fa fa-envelope";

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg(
        "Search for an email template by path or description...",
    );

    public override order = "path";

    protected override async apiEndpoint(): Promise<PaginatedResponse<EmailTemplate>> {
        return aki(StagesApi).stagesEmailTemplatesList(await this.defaultEndpointConfig());
    }

    protected override columns: TableColumn[] = [
        [msg("Template"), "path"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override groupBy(items: EmailTemplate[]): GroupResult<EmailTemplate>[] {
        return groupBy(items, (template) => (template.managed ? msg("Built-in") : msg("Custom")));
    }

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;

        return html`<ak-forms-delete-bulk
            object-label=${msg("Email template(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: EmailTemplate) => [{ key: msg("Path"), value: item.path }]}
            .usedBy=${(item: EmailTemplate) => {
                return aki(StagesApi).stagesEmailTemplatesUsedByList({
                    uuid: item.uuid,
                });
            }}
            .delete=${(item: EmailTemplate) => {
                return aki(StagesApi).stagesEmailTemplatesDestroy({
                    uuid: item.uuid,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: EmailTemplate): SlottedTemplateResult[] {
        return [
            html`<div><code>${item.path}</code></div>
                <small>${item.managed ? item.displayName : item.description}</small>`,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(EmailTemplateForm, item.uuid, item.path)}
                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikStagesEmailEmailtemplate}
                    objectPk=${item.uuid}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(EmailTemplateForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-email-template-list": EmailTemplateListPage;
    }
}
