import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { PreventFormSubmit } from "#elements/forms/helpers";
import { showMessage } from "#elements/messages/MessageContainer";

import { AdminApi, AdminFileListUsageEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

// Same regex is used in the backend as well
const VALID_FILE_NAME_PATTERN = /^[a-zA-Z0-9._/-]+$/;

@customElement("ak-file-upload-form")
export class FileUploadForm extends Form<Record<string, unknown>> {
    @property({ type: String, useDefault: true })
    public usage: AdminFileListUsageEnum = AdminFileListUsageEnum.Media;

    @state()
    protected selectedFile: File | null = null;

    #formRef = createRef<HTMLFormElement>();

    #fileChangeListener = (e: Event) => {
        const input = e.target as HTMLInputElement;
        if (input.files?.length) {
            this.selectedFile = input.files[0];
        } else {
            this.selectedFile = null;
        }
    };

    protected clearFileInput() {
        this.selectedFile = null;
        this.#formRef.value?.reset();
    }

    public override async send(data: Record<string, unknown>): Promise<void> {
        if (!this.selectedFile) {
            throw new PreventFormSubmit("Selected file not provided", this);
        }

        if (!VALID_FILE_NAME_PATTERN.test(this.selectedFile.name)) {
            throw new Error(
                msg("Filename can only contain letters, numbers, dots, hyphens, and underscores"),
            );
        }

        const api = new AdminApi(DEFAULT_CONFIG);
        const customName = typeof data.fileName === "string" ? data.fileName.trim() : "";

        // If custom name provided, validate and append original extension
        let finalName = this.selectedFile.name;
        if (customName) {
            if (!VALID_FILE_NAME_PATTERN.test(customName)) {
                throw new Error(
                    msg(
                        "Filename can only contain letters, numbers, dots, hyphens, and underscores",
                    ),
                );
            }
            const ext = this.selectedFile.name.substring(this.selectedFile.name.lastIndexOf("."));
            finalName = customName + ext;
        }

        return api
            .adminFileCreate({
                file: this.selectedFile,
                name: finalName,
                usage: this.usage,
            })
            .then(() => {
                showMessage({
                    level: MessageLevel.success,
                    message: msg("File uploaded successfully"),
                });

                this.reset();
            })
            .catch((error) => {
                throw error;
            })
            .finally(() => {
                this.clearFileInput();
            });
    }

    renderForm() {
        return html`
            <form ${ref(this.#formRef)} class="pf-c-form pf-m-horizontal">
                <ak-form-element-horizontal label=${msg("File")} required>
                    <input
                        type="file"
                        class="pf-c-form-control"
                        id="file-input"
                        required
                        @change=${this.#fileChangeListener}
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${msg("File Name")} name="fileName">
                    <input
                        type="text"
                        class="pf-c-form-control"
                        placeholder=${msg("Leave empty to use original filename")}
                    />
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Optionally rename the file (without extension). Leave empty to keep the original filename.",
                        )}
                    </p>
                </ak-form-element-horizontal>
            </form>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-file-upload-form": FileUploadForm;
    }
}
