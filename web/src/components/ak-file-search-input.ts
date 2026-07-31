import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import HostStyles from "./ak-file-search-input.css";

import { aki } from "#common/api/client";
import { docLink, globalAK } from "#common/global";

import { AKElement } from "#elements/Base";

import { AKLabel } from "#components/ak-label";

import { AdminApi, FileList, UsageEnum } from "@goauthentik/api";
import { IDGenerator } from "@goauthentik/core/id";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const renderElement = (item: FileList) => item.name;
const renderValue = (item?: FileList | null) => item?.name;

/**
 * File Search Input Component
 *
 * Search/select dropdown for files from authentik.admin.files storage.
 * Supports uploaded files, static files, and external URLs/Font Awesome icons via PassthroughBackend.
 */
@customElement("ak-file-search-input")
export class AKFileSearchInput extends AKElement {
    public static hostStyles = [HostStyles];

    // Render into the lightDOM
    protected createRenderRoot() {
        return this;
    }

    @property({ type: String })
    public name: string | null = null;

    @property({ type: String })
    public label: string | null = null;

    @property({ type: String })
    public value: string = "";

    @property({ type: Boolean })
    public required = false;

    @property({ type: Boolean })
    public blankable = false;

    @property({ type: String })
    public help: string | null = null;

    @property({ type: String, useDefault: true })
    public usage: UsageEnum = UsageEnum.Media;

    @property({ type: String, reflect: false })
    public fieldID?: string = IDGenerator.elementID().toString();

    #selected = (item: FileList) => {
        return this.value === item.name;
    };

    #changeListener(event: CustomEvent<{ value: FileList | null }>) {
        this.value = event.detail.value?.name ?? "";
    }

    async #fetch(query?: string): Promise<FileList[]> {
        const results = await aki(AdminApi).adminFileList({
            usage: this.usage,
            ...(query ? { search: query.toLocaleLowerCase() } : {}),
        });

        // Custom URLs and Font Awesome icons are valid values, but are not returned by the files
        // API. Include the current value on the initial load so the control can select it.
        if (!query && this.value && !results.some((item) => item.name === this.value)) {
            return [
                {
                    name: this.value,
                    url: this.value,
                    mimeType: "",
                },
                ...results,
            ];
        }

        return results;
    }

    render() {
        return html` <ak-form-element-horizontal name=${ifDefined(this.name ?? undefined)}>
            ${AKLabel(
                {
                    slot: "label",
                    className: "pf-c-form__group-label",
                    htmlFor: this.fieldID,
                    required: this.required,
                },
                this.label,
            )}

            <ak-search-select
                style="width: 100%;"
                .fieldID=${this.fieldID}
                .fetchObjects=${this.#fetch.bind(this)}
                .renderElement=${renderElement}
                .value=${renderValue}
                .selected=${this.#selected}
                placeholder=${msg("Select a file or enter a value...", {
                    id: "file-picker.value.placeholder",
                })}
                ?blankable=${this.blankable}
                creatable
                @ak-change=${this.#changeListener}
            >
            </ak-search-select>
            <p class="pf-c-form__helper-text">
                ${this.help
                    ? this.help
                    : msg("Choose an existing file, or enter a URL or Font Awesome icon.", {
                          id: "file-picker.value.description",
                      })}
                <span class="ak-file-search-input__actions">
                    <a
                        target="_blank"
                        rel="noopener noreferrer"
                        href=${`${globalAK().api.base}if/admin/#/files`}
                    >
                        ${msg("Upload file", { id: "file-picker.upload-link.label" })}
                    </a>
                    <span class="ak-file-search-input__separator" aria-hidden="true">·</span>
                    <a
                        target="_blank"
                        rel="noopener noreferrer"
                        href=${docLink("/customize/file-picker/")}
                    >
                        ${msg("Supported values", {
                            id: "file-picker.documentation-link.label",
                        })}
                    </a>
                </span>
            </p>
        </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-file-search-input": AKFileSearchInput;
    }
}
