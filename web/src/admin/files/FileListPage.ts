import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#elements/EmptyState";

import { aki } from "#common/api/client";
import { createPaginatedResponse } from "#common/api/responses";
import { docLink } from "#common/global";

import { ModalInvokerButton } from "#elements/dialogs";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { getURLParam } from "#elements/router/RouteMatch";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { FileUploadForm } from "#admin/files/FileUploadForm";

import { AdminApi, CapabilitiesEnum, FileList, UsageEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

export type FileListItem = Pick<FileList, "name" | "url" | "mimeType">;

export type FileListOrderKey = "name" | "mimeType";

@customElement("ak-files-list")
export class FileListPage extends WithCapabilitiesConfig(TablePage<FileListItem>) {
    public override checkbox = true;
    public override clearOnRefresh = true;

    protected override searchEnabled = true;
    public override pageTitle = msg("Files");
    public override pageDescription = msg("Manage uploaded files.");
    public override pageIcon = "pf-icon pf-icon-folder-open";
    public override searchPlaceholder = msg("Search for a file by name...");

    @property({ type: String, useDefault: true })
    public order: FileListOrderKey = "name";

    public override firstUpdated(changed: PropertyValues<this>): void {
        super.firstUpdated(changed);

        if (getURLParam("upload", false) && this.can(CapabilitiesEnum.CanSaveMedia)) {
            FileUploadForm.showModal();
        }
    }

    async apiEndpoint(): Promise<PaginatedResponse<FileListItem>> {
        const api = aki(AdminApi);
        const items = await api.adminFileList({
            usage: UsageEnum.Media,
            manageableOnly: true,
            ...(this.search ? { search: this.search } : {}),
        });

        // Wrap array response in paginated response structure
        return createPaginatedResponse(items);
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Type")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected() {
        if (!this.can(CapabilitiesEnum.CanSaveMedia)) {
            return null;
        }

        const disabled = !this.selectedElements.length;
        const count = this.selectedElements.length;

        return html`<ak-forms-delete-bulk
            object-label=${count === 1 ? msg("file") : msg("files")}
            .objects=${this.selectedElements}
            .metadata=${(item: FileListItem) => {
                return [
                    { key: msg("Name"), value: item.name },
                    { key: msg("Type"), value: item.mimeType },
                ];
            }}
            .usedBy=${(item: FileListItem) => {
                return aki(AdminApi).adminFileUsedByList({
                    name: item.name,
                });
            }}
            .delete=${(item: FileListItem) => {
                return aki(AdminApi).adminFileDestroy({
                    name: item.name,
                    usage: UsageEnum.Media,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: FileListItem): SlottedTemplateResult[] {
        return [
            item.name,
            item.mimeType || msg("-"),
            html`<div>
                <a
                    class="pf-c-button pf-m-plain"
                    target="_blank"
                    href=${item.url}
                    rel="noopener noreferrer"
                >
                    <pf-tooltip position="top" content=${msg("Open")}>
                        <i class="fas fa-external-link-alt" aria-hidden="true"></i>
                    </pf-tooltip>
                </a>
            </div>`,
        ];
    }

    protected renderEmpty(inner?: TemplateResult) {
        if (this.can(CapabilitiesEnum.CanSaveMedia)) {
            return super.renderEmpty(inner);
        }
        return super.renderEmpty(
            html`<ak-empty-state icon=${this.pageIcon}
                ><span>${msg("Configured file backend does not support file management.")}</span>
                <div slot="body">
                    ${msg("Please ensure the data folder is mounted or S3 storage is configured.")}
                </div>
                <div slot="primary">
                    <a
                        target="_blank"
                        class="pf-c-button pf-m-secondary"
                        href=${docLink("/install-config/configuration/#storage-settings")}
                        >${msg("Learn more")}</a
                    >
                </div>
            </ak-empty-state>`,
        );
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(FileUploadForm);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-files-list": FileListPage;
    }
}
