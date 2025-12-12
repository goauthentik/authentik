import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { DataExport, ReportsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-data-export-list")
export class DataExportListPage extends TablePage<DataExport> {
    protected override searchEnabled = true;
    protected override emptyStateMessage = msg(
        "To create a data export, navigate to Directory > Users or to Events > Logs.",
    );
    public pageTitle = msg("Data Exports");
    public pageDescription = msg("Manage past data exports.");
    public pageIcon = "pf-icon pf-icon-export";

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override expandable = true;

    @property({ type: String })
    public order = "-requested_on";

    async apiEndpoint(): Promise<PaginatedResponse<DataExport>> {
        return new ReportsApi(DEFAULT_CONFIG).reportsExportsList(
            await this.defaultEndpointConfig(),
        );
    }

    protected columns: TableColumn[] = [
        [msg("Data type"), "content_type__model"],
        [msg("Requested by"), "requested_by"],
        [msg("Creation date"), "requested_on"],
        [msg("Completed"), "completed"],
        [msg("Actions"), null, msg("Row actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html` <ak-forms-delete-bulk
            objectLabel=${msg("Data export(s)")}
            .objects=${this.selectedElements}
            .delete=${(item: DataExport) => {
                return new ReportsApi(DEFAULT_CONFIG).reportsExportsDestroy({
                    id: item.id,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: DataExport): SlottedTemplateResult[] {
        return [
            html`${item.contentType.model}`,
            html`<a href="#/identity/users/${item.requestedBy.pk}"
                >${item.requestedBy.username}</a
            >`,
            Timestamp(item.requestedOn),
            html`${item.completed ? msg("Yes") : msg("No")}`,
            item.completed && item.fileUrl
                ? html`<div>
                      <a href="${item.fileUrl}">
                          <pf-tooltip position="top" content=${msg("Download")}>
                              <i class="fas fa-download" aria-hidden="true"></i>
                          </pf-tooltip>
                      </a>
                  </div>`
                : html``,
        ];
    }

    renderExpanded(item: DataExport): TemplateResult {
        return html` <dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-card__title">${msg("Query parameters")}</div>
            <div class="pf-c-card__body">
                <code>${JSON.stringify(item.queryParams, null, 4)}</code>
            </div>
        </dl>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-data-export-list": DataExportListPage;
    }
}
