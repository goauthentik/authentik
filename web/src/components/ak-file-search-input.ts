import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import { AKLabel } from "#components/ak-label";

import { AdminApi, AdminFileListUsageEnum } from "@goauthentik/api";
import { IDGenerator } from "@goauthentik/core/id";

import { msg } from "@lit/localize";
import { html } from "lit";
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
 * Search/select dropdown for files from authentik.admin.files storage.
 * Supports uploaded files, static files, and external URLs/Font Awesome icons via PassthroughBackend.
 */
@customElement("ak-file-search-input")
export class AkFileSearchInput extends AKElement {
    // Render into the lightDOM
    protected createRenderRoot() {
        return this;
    }

    @property({ type: String })
    public name!: string;

    @property({ type: String })
    public label: string | null = null;

    @property({ type: String })
    public value?: string;

    @property({ type: Boolean })
    public required = false;

    @property({ type: Boolean })
    public blankable = false;

    @property({ type: String })
    public help: string | null = null;

    @property({ type: String, useDefault: true })
    public usage: AdminFileListUsageEnum = AdminFileListUsageEnum.Media;

    @property({ type: String, reflect: false })
    public fieldID?: string = IDGenerator.elementID().toString();

    #selected = (item: FileItem) => {
        return this.value === item.name;
    };

    public override firstUpdated() {
        // If we have a value but it's not in the fetched results (like fa:// or custom URL),
        // the search-select won't show it. We need to add it to the initial fetch.
        if (this.value) {
            // Search-select will call #fetch and then try to select using #selected
            // And then if the value isn't found in results, creatable mode will handle it
        }
    }

    async #fetch(query?: string): Promise<FileItem[]> {
        const api = new AdminApi(DEFAULT_CONFIG);
        return api
            .adminFileList({
                usage: this.usage as AdminFileListUsageEnum,
                ...(query ? { search: query } : {}),
            })
            .then((response) => {
                const fileResponse = response as unknown as FileItem[];

                if (!fileResponse || !Array.isArray(fileResponse)) {
                    console.error("Invalid response format from files API", fileResponse);
                    return [];
                }

                let results = fileResponse;

                // If we have a current value and it's not in the results (e.g., fa:// or custom URL),
                // add it as a synthetic item so it shows up as selected
                if (this.value && !results.find((item) => item.name === this.value)) {
                    results = [
                        {
                            name: this.value,
                            url: this.value,
                            mime_type: "",
                            size: 0,
                            usage: this.usage,
                        },
                        ...results,
                    ];
                }

                return results;
            })
            .catch(async (error) => {
                const parsedError = await parseAPIResponseError(error);
                console.error(msg("Failed to fetch files"), pluckErrorDetail(parsedError));
                return [];
            });
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
                      ${msg(
                          "You can also enter a URL (https://...), Font Awesome icon (fa://fa-icon-name), or upload a new file.",
                      )}
                  </p>`}
        </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-file-search-input": AkFileSearchInput;
    }
}
