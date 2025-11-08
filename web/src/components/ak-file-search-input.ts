import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { AKLabel } from "#components/ak-label";
import { IDGenerator } from "#packages/core/id";

import { FilesApi, FileUploadRequestUsageEnum } from "@goauthentik/api";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

interface FileItem {
    name: string;
    url: string;
    mime_type: string;
    size: number;
    usage: string;
}

const renderElement = (item: FileItem) => item.name;
const renderValue = (item: FileItem | undefined) => item?.name;

/**
 * File Search Input Component
 *
 * Search/select dropdown for files from authentik.files storage.
 * Supports uploaded files, static files, and external URLs/Font Awesome icons via PassthroughBackend.
 */
@customElement("ak-file-search-input")
export class AkFileSearchInput extends AKElement {
    // Render into the lightDOM
    protected createRenderRoot() {
        return this;
    }

    @property({ type: String })
    name!: string;

    @property({ type: String })
    label: string | null = null;

    @property({ type: String })
    value?: string;

    @property({ type: Boolean })
    required = false;

    @property({ type: Boolean })
    blankable = false;

    @property({ type: String })
    help: string | null = null;

    @property({ type: String })
    usage: FileUploadRequestUsageEnum = FileUploadRequestUsageEnum.Media;

    @property({ type: Array })
    specialUsages: string[] = [];

    @property({ type: String, reflect: false })
    public fieldID?: string = IDGenerator.elementID().toString();

    #selected = (item: FileItem) => {
        return this.value === item.name;
    };

    async #fetch(query?: string): Promise<FileItem[]> {
        const api = new FilesApi(DEFAULT_CONFIG);
        const response: any = await api.filesList({
            usage: this.usage as any,
            ...(query ? { search: query } : {}),
            ...(this.specialUsages.length > 0 ? { specialUsages: this.specialUsages.join(",") } : {}),
        });

        return response.results || [];
    }

    render() {
        return html` <ak-form-element-horizontal name=${this.name}>
            <div slot="label" class="pf-c-form__group-label">
                ${AKLabel({ htmlFor: this.fieldID, required: this.required }, this.label)}
            </div>

            <ak-search-select
                style="width: 100%;"
                .fieldID=${this.fieldID}
                .fetchObjects=${this.#fetch.bind(this)}
                .renderElement=${renderElement}
                .value=${renderValue}
                .selected=${this.#selected}
                ?blankable=${this.blankable}
                creatable
            >
            </ak-search-select>
            ${this.help
                ? html`<p class="pf-c-form__helper-text">${this.help}</p>`
                : html`<p class="pf-c-form__helper-text">
                      You can also enter a URL (https://...), Font Awesome icon (fa://fa-icon-name), or upload a new file.
                  </p>`}
        </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-file-search-input": AkFileSearchInput;
    }
}
