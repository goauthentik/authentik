import "#admin/files/FileUploadForm";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { formatBytes } from "#common/utils/bytes";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import {
    AdminApi,
    AdminFileDestroyUsageEnum,
    AdminFileListUsageEnum,
    UsageEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

interface FileItem {
    name: string;
    url: string;
    mime_type: string;
    size: number;
    usage: UsageEnum;
}

@customElement("ak-files-list")
export class FileListPage extends TablePage<FileItem> {
    checkbox = true;
    clearOnRefresh = true;

    protected override searchEnabled = true;
    public pageTitle = msg("Files");
    public pageDescription = msg("Manage uploaded files.");
    public pageIcon = "pf-icon pf-icon-folder-open";

    @property()
    order = "name";

    @property()
    usage: UsageEnum = UsageEnum.Media;

    async apiEndpoint(): Promise<PaginatedResponse<FileItem>> {
        const api = new AdminApi(DEFAULT_CONFIG);
        const items = (await api.adminFileList({
            usage: this.usage as AdminFileListUsageEnum,
            ...(this.search ? { search: this.search } : {}),
        })) as unknown as FileItem[];

        // Wrap array response in paginated response structure
        return {
            pagination: {
                next: 0,
                previous: 0,
                count: items.length,
                current: 1,
                total_pages: 1,
                start_index: 1,
                end_index: items.length,
            },
            results: items,
        };
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Type")],
        [msg("Size")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        const count = this.selectedElements.length;
        return html`<ak-forms-delete-bulk
            objectLabel=${count === 1 ? msg("file") : msg("files")}
            .objects=${this.selectedElements}
            .metadata=${(item: FileItem) => {
                return [
                    { key: msg("Name"), value: item.name },
                    { key: msg("Type"), value: item.mime_type },
                ];
            }}
            .delete=${(item: FileItem) => {
                return new AdminApi(DEFAULT_CONFIG).adminFileDestroy({
                    name: item.name,
                    usage: item.usage as AdminFileDestroyUsageEnum,
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
            html`<div>${item.mime_type || "-"}</div>`,
            html`<div>${formatBytes(item.size)}</div>`,
            html`<div>
                <a
                    class="pf-c-button pf-m-secondary"
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

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit">${msg("Upload")}</span>
                <span slot="header">${msg("Upload File")}</span>
                <ak-file-upload-form slot="form" .usage=${this.usage}> </ak-file-upload-form>
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
