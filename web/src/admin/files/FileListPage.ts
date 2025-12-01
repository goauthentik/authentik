import "#admin/files/FileUploadForm";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { AdminApi, AdminFileListUsageEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

export interface FileItem {
    name: string;
    url: string;
    mimeType: string;
}

export type FileListOrderKey = "name" | "mimeType";

@customElement("ak-files-list")
export class FileListPage extends TablePage<FileItem> {
    public override checkbox = true;
    public override clearOnRefresh = true;

    protected override searchEnabled = true;
    public override pageTitle = msg("Files");
    public override pageDescription = msg("Manage uploaded files.");
    public override pageIcon = "pf-icon pf-icon-folder-open";

    @property({ type: String, useDefault: true })
    public order: FileListOrderKey = "name";

    async apiEndpoint(): Promise<PaginatedResponse<FileItem>> {
        const api = new AdminApi(DEFAULT_CONFIG);
        // Cast necessary: API returns File objects but we only use name, url, and mimeType properties
        const items = (await api.adminFileList({
            usage: AdminFileListUsageEnum.Media,
            manageableOnly: true,
            ...(this.search ? { search: this.search } : {}),
        })) as unknown as FileItem[];

        // Wrap array response in paginated response structure
        return {
            pagination: {
                next: 0,
                previous: 0,
                count: items.length,
                current: 1,
                totalPages: 1,
                startIndex: 1,
                endIndex: items.length,
            },
            results: items,
        };
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Type")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = !this.selectedElements.length;
        const count = this.selectedElements.length;
        return html`<ak-forms-delete-bulk
            objectLabel=${count === 1 ? msg("file") : msg("files")}
            .objects=${this.selectedElements}
            .metadata=${(item: FileItem) => {
                return [
                    { key: msg("Name"), value: item.name },
                    { key: msg("Type"), value: item.mimeType },
                ];
            }}
            .usedBy=${(item: FileItem) => {
                return new AdminApi(DEFAULT_CONFIG).adminFileUsedByList({
                    name: item.name,
                });
            }}
            .delete=${(item: FileItem) => {
                return new AdminApi(DEFAULT_CONFIG).adminFileDestroy({
                    name: item.name,
                    usage: AdminFileListUsageEnum.Media,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: FileItem): SlottedTemplateResult[] {
        return [
            html`<div>${item.name}</div>`,
            html`<div>${item.mimeType || msg("-")}</div>`,
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

    protected renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Upload")}</span>
                <span slot="header">${msg("Upload File")}</span>
                <ak-file-upload-form slot="form"> </ak-file-upload-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">
                    ${msg("Upload File")}
                </button>
            </ak-forms-modal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-files-list": FileListPage;
    }
}
