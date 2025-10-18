import "#admin/files/FileUploadForm";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { FilesApi, FileUploadRequestUsageEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

interface FileItem {
    name: string;
    url: string;
    mime_type: string;
    size: number;
    usage: string;
}

interface UsageType {
    value: string;
    label: string;
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
    usage: FileUploadRequestUsageEnum = FileUploadRequestUsageEnum.Media;

    @property({ type: Array })
    usageTypes: UsageType[] = [];

    async firstUpdated(): Promise<void> {
        super.firstUpdated();
        await this.fetchUsageTypes();
    }

    async fetchUsageTypes(): Promise<void> {
        const api = new FilesApi(DEFAULT_CONFIG);
        const response = await api.filesUsagesList();
        this.usageTypes = response as UsageType[];
    }

    async apiEndpoint(): Promise<PaginatedResponse<FileItem>> {
        const api = new FilesApi(DEFAULT_CONFIG);
        const response: any = await api.filesList({
            usage: this.usage as any,
            ...(this.search ? { search: this.search } : {}),
        });

        return response as PaginatedResponse<FileItem>;
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Type")],
        [msg("Size")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbar(): TemplateResult {
        return html`
            <select
                class="pf-c-form-control"
                @change=${(e: Event) => {
                    const target = e.target as HTMLSelectElement;
                    this.usage = target.value as FileUploadRequestUsageEnum;
                    this.fetch();
                }}
            >
                ${this.usageTypes.map(
                    (usageType) => html`
                        <option value=${usageType.value} ?selected=${this.usage === usageType.value}>
                            ${usageType.label}
                        </option>
                    `,
                )}
            </select>
            ${super.renderToolbar()}
        `;
    }

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
                return new FilesApi(DEFAULT_CONFIG).filesDeleteDestroy({
                    name: item.name,
                    usage: item.usage as any,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: FileItem): SlottedTemplateResult[] {
        const formatBytes = (bytes: number) => {
            if (bytes === 0) return "0 B";
            const k = 1024;
            const sizes = ["B", "KB", "MB", "GB"];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
        };

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
