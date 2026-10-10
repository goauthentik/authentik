import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/ak-search-select";
import HostStyles from "./ak-file-search-input.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";
import { docLink } from "#common/global";

import { AKElement } from "#elements/Base";
import { renderModal } from "#elements/dialogs";
import { AKFormSubmittedEvent } from "#elements/forms/events";
import type { SearchSelect } from "#elements/forms/SearchSelect/ak-search-select";
import type { SearchSelectChangeEvent } from "#elements/forms/SearchSelect/events";
import type { SearchSelectSource } from "#elements/forms/SearchSelect/shared";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { AKLabel } from "#components/ak-label";

import { FileUploadForm } from "#admin/files/FileUploadForm";

import { ConsoleLogger } from "#logger/browser";

import { AdminApi, AdminFileCreateRequest, FileList, UsageEnum } from "@goauthentik/api";
import { IDGenerator } from "@goauthentik/core/id";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

const fileSources = new Map<UsageEnum, SearchSelectSource<FileList>>();

/**
 * A search select source for files with the given usage.
 */
export function fileSource(usage: UsageEnum): SearchSelectSource<FileList> {
    const cached = fileSources.get(usage);

    if (cached) return cached;

    const source: SearchSelectSource<FileList> = {
        fetchObjects: (query) =>
            aki(AdminApi).adminFileList({
                usage,
                ...(query ? { search: query.toLocaleLowerCase() } : {}),
            }),
        keyOf: (file) => file.name,
        labelOf: (file) => file.name,
    };

    fileSources.set(usage, source);

    return source;
}

/**
 * File Search Input Component
 *
 * Search/select dropdown for files from authentik.admin.files storage. Supports uploaded files,
 * static files, and external URLs/Font Awesome icons via PassthroughBackend.
 */
@customElement("ak-file-search-input")
export class AKFileSearchInput extends AKElement {
    public static hostStyles = [PFButton, PFInputGroup, HostStyles];

    // Render into the lightDOM
    protected createRenderRoot() {
        return this;
    }

    protected logger = ConsoleLogger.prefix(`model-form/${this.localName}`);

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

    protected fileSearchRef = createRef<SearchSelect<FileList>>();

    protected openFileUploadModal = (invocationEvent?: Event) => {
        invocationEvent?.stopPropagation();

        const fileUploadForm = new FileUploadForm();

        let createdFile: AdminFileCreateRequest | null = null;

        fileUploadForm.addEventListener(AKFormSubmittedEvent.eventName, (event) => {
            createdFile = (event as AKFormSubmittedEvent<AdminFileCreateRequest>).response;
        });

        return renderModal(fileUploadForm, {
            invokerElement:
                invocationEvent?.target instanceof HTMLElement ? invocationEvent.target : this,
            size: PFSize.Medium,
            onDispose: (disposeEvent) => {
                const { target } = disposeEvent || {};

                if (!(target instanceof HTMLDialogElement) || target.returnValue !== "submitted") {
                    return;
                }

                const fileSearch = this.fileSearchRef.value;

                if (!fileSearch) {
                    this.logger.error(
                        "Failed to refresh file search after creating new file. No file search found.",
                    );

                    return;
                }

                // Refresh the file search and select the newly created file.
                if (!createdFile) {
                    this.logger.error(
                        "File upload form closed as submitted, but no created file was captured.",
                    );

                    return;
                }

                this.value = createdFile.name ?? "";
                fileSearch.value = this.value;

                return fileSearch.refresh();
            },
        });
    };

    protected changeListener = (event: SearchSelectChangeEvent<FileList>) => {
        this.value = (event.currentTarget as SearchSelect<FileList>).value;
    };

    protected override render(): SlottedTemplateResult {
        const uploadLabel = msg("Upload file", { id: "file-picker.upload-link.label" });

        return html`<ak-form-element-horizontal name=${ifPresent(this.name)}>
            ${AKLabel(
                {
                    slot: "label",
                    className: "pf-c-form__group-label",
                    htmlFor: this.fieldID,
                    required: this.required,
                },
                this.label,
            )}

            <div class="pf-c-input-group">
                <ak-search-select
                    ${ref(this.fileSearchRef)}
                    class="ak-file-search-input__select"
                    id=${ifPresent(this.fieldID)}
                    name=${ifPresent(this.name)}
                    .source=${fileSource(this.usage)}
                    .value=${this.value}
                    placeholder=${msg("Select a file or enter a value...", {
                        id: "file-picker.value.placeholder",
                    })}
                    ?required=${this.required}
                    ?blankable=${this.blankable}
                    creatable
                    @ak-change=${this.changeListener}
                    action-label=${uploadLabel}
                    @ak-search-select-action=${this.openFileUploadModal}
                ></ak-search-select>
                <button
                    @click=${this.openFileUploadModal}
                    type="button"
                    class="pf-c-button pf-m-control"
                    aria-label=${uploadLabel}
                    title=${uploadLabel}
                >
                    <i class="fas fa-upload" aria-hidden="true"></i>
                </button>
            </div>
            <p class="pf-c-form__helper-text">
                ${
                    this.help
                        ? this.help
                        : msg("Choose an existing file, or enter a URL or Font Awesome icon.", {
                              id: "file-picker.value.description",
                          })
                }
                <a
                    class="ak-file-search-input__documentation"
                    target="_blank"
                    rel="noopener noreferrer"
                    href=${docLink("/customize/file-picker/")}
                >
                    ${msg("Supported values", {
                        id: "file-picker.documentation-link.label",
                    })}
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
