import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { docLink } from "#common/global";

import { AKElement } from "#elements/Base";

import { AKLabel } from "#components/ak-label";

import { AdminApi, UsageEnum } from "@goauthentik/api";
import { IDGenerator } from "@goauthentik/core/id";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

interface FileItem {
    name: string;
    url: string;
    mime_type: string;
    size: number;
    usage: string;
}

const inFlightFetches = new Map<string, Promise<FileItem[]>>();

const renderElement = (item: FileItem) => item.name;
const renderValue = (item?: FileItem | null) => item?.name;

function createCustomFileItem(name: string, usage: UsageEnum): FileItem {
    return {
        name,
        url: name,
        mime_type: "",
        size: 0,
        usage,
    };
}

/**
 * File Search Input Component
 *
 * Search/select dropdown for files from authentik.admin.files storage.
 * Supports uploaded files, static files, and external URLs/Font Awesome icons via PassthroughBackend.
 */
@customElement("ak-file-search-input")
export class AKFileSearchInput extends AKElement {
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

    #selected = (item: FileItem) => {
        return this.value === item.name;
    };

    async #fetchFiles(query?: string): Promise<FileItem[]> {
        const cacheKey = `${this.usage}:${query ?? ""}`;
        let fetchPromise = inFlightFetches.get(cacheKey);
        if (!fetchPromise) {
            const api = aki(AdminApi);
            fetchPromise = api
                .adminFileList({
                    usage: this.usage as UsageEnum,
                    ...(query ? { search: query } : {}),
                })
                .then((response) => {
                    // Cast necessary: API returns File objects but we only use name, url, mime_type, size, and usage properties
                    const fileResponse = response as unknown as FileItem[];

                    if (!fileResponse || !Array.isArray(fileResponse)) {
                        console.error("Invalid response format from files API", fileResponse);
                        return [];
                    }

                    return fileResponse;
                })
                .catch(async (error) => {
                    const parsedError = await parseAPIResponseError(error);
                    console.error(msg("Failed to fetch files"), pluckErrorDetail(parsedError));
                    return [];
                })
                .finally(() => {
                    inFlightFetches.delete(cacheKey);
                });
            inFlightFetches.set(cacheKey, fetchPromise);
        }

        return fetchPromise;
    }

    async #fetch(query?: string): Promise<FileItem[]> {
        return this.#fetchFiles(query).then((fileResponse) => {
            let results = fileResponse;

            if (!query && this.value && !results.find((item) => item.name === this.value)) {
                results = [createCustomFileItem(this.value, this.usage), ...results];
            }

            return results;
        });
    }

    #createObject = (value: string): FileItem => {
        return createCustomFileItem(value, this.usage);
    };

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
                .createObject=${this.#createObject}
                ?blankable=${this.blankable}
                creatable
            >
            </ak-search-select>
            <p class="pf-c-form__helper-text">
                ${this.help
                    ? this.help
                    : msg(
                          "You can also enter a URL (https://...), Font Awesome icon (fa://fa-icon-name), or upload a new file.",
                      )}
                <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href=${docLink("/customize/file-picker/")}
                >
                    ${msg("See documentation for supported values.")}
                </a>
            </p>
        </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-file-search-input": AKFileSearchInput;
    }
}
