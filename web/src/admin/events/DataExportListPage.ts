import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/TaskList";
import "#components/ak-status-label";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import renderDescriptionList, { DescriptionPair } from "#components/DescriptionList";

import { DataExport, ReportsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-data-export-list")
export class DataExportListPage extends TablePage<DataExport> {
    protected override searchEnabled = true;
    public pageTitle = msg("Data Exports");
    public pageDescription = msg("Manage past data exports.");
    public pageIcon = "pf-icon pf-icon-export";

    public override checkbox = true;
    public override clearOnRefresh = true;
    public override expandable = true;

    @property({ type: String })
    public order = "-requested_on";

    static styles = [...TablePage.styles, PFDescriptionList];

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
        return html`<ak-forms-delete-bulk
            object-label=${msg("Data export(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: DataExport) => {
                return [
                    { key: msg("Data type"), value: item.contentType.verboseNamePlural },
                    { key: msg("Requested by"), value: item.requestedBy.username },
                    { key: msg("Creation date"), value: Timestamp(item.requestedOn) },
                ];
            }}
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
            html`${item.contentType.verboseNamePlural}`,
            html`<a href="#/identity/users/${item.requestedBy.pk}"
                >${item.requestedBy.username}</a
            >`,
            Timestamp(item.requestedOn),
            html`${item.completed
                ? html`<ak-label color=${PFColor.Green}>${msg("Finished")}</ak-label>`
                : html`<ak-label color=${PFColor.Grey}>${msg("Queued")}</ak-label>`}`,
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
                ${renderDescriptionList(
                    Object.keys(item.queryParams)
                        .filter((key) => {
                            if (key === "page" || key === "pageSize") return false;

                            return !!item.queryParams[key];
                        })
                        .map((key): DescriptionPair => {
                            return [key, html`<pre>${item.queryParams[key]}</pre>`];
                        }),
                    { horizontal: true, compact: true },
                )}
            </div>
        </dl>`;
    }

    protected renderEmpty(_inner?: TemplateResult): TemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state icon=${this.pageIcon}
                ><span
                    >${msg(
                        html`To create a data export, navigate to
                            <a href="#/identity/users">Directory > Users</a> or to
                            <a href="#/events/log">Events > Logs</a>.`,
                    )}</span
                >
            </ak-empty-state>`,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-data-export-list": DataExportListPage;
    }
}
