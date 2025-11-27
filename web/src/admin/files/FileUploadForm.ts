import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { PreventFormSubmit } from "#elements/forms/helpers";
import { showMessage } from "#elements/messages/MessageContainer";

import { AdminApi, AdminFileListUsageEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-file-upload-form")
export class FileUploadForm extends Form<Record<string, unknown>> {
    @property({ type: String, useDefault: true })
    public usage: AdminFileListUsageEnum = AdminFileListUsageEnum.Media;

    @state()
    protected selectedFile: File | null = null;

    private clearFileInput() {
        this.selectedFile = null;
        const fileInput = this.shadowRoot?.querySelector<HTMLInputElement>("#file-input");
        if (fileInput) {
            fileInput.value = "";
        }
    }

    public override async send(): Promise<void> {
        if (!this.selectedFile) {
            throw new PreventFormSubmit("Selected file not provided", this);
        }

        // Validate filename contains only safe characters (a-zA-Z0-9._-)
        const ValidFilenameRegex = /^[a-zA-Z0-9._-]+$/;
        if (!ValidFilenameRegex.test(this.selectedFile.name)) {
            throw new Error(
                msg("Filename can only contain letters, numbers, dots, hyphens, and underscores"),
            );
        }

        const api = new AdminApi(DEFAULT_CONFIG);
        const customName = this.shadowRoot
            ?.querySelector<HTMLInputElement>("#file-name")
            ?.value?.trim();

        // If custom name provided, validate and append original extension
        let finalName = this.selectedFile.name;
        if (customName) {
            if (!ValidFilenameRegex.test(customName)) {
                throw new Error(
                    msg(
                        "Filename can only contain letters, numbers, dots, hyphens, and underscores",
                    ),
                );
            }
            const ext = this.selectedFile.name.substring(this.selectedFile.name.lastIndexOf("."));
            finalName = customName + ext;
        }

        try {
            await api.adminFileCreate({
                file: this.selectedFile,
                name: finalName,
                usage: this.usage,
            });

            showMessage({
                level: MessageLevel.success,
                message: msg("File uploaded successfully"),
            });

            // Clear the file input and state on success
            this.clearFileInput();
            this.reset();
        } catch (error) {
            // Clear the file input on error too
            this.clearFileInput();
            throw error;
        }
    }

    renderForm() {
        return html`
            <form class="pf-c-form pf-m-horizontal">
                <div class="pf-c-form__group">
                    <label class="pf-c-form__label" for="file-input">
                        <span class="pf-c-form__label-text">${msg("File")}</span>
                        <span class="pf-c-form__label-required" aria-hidden="true">*</span>
                    </label>
                    <input
                        type="file"
                        class="pf-c-form-control"
                        id="file-input"
                        name="file"
                        required
                        @change=${(e: Event) => {
                            const input = e.target as HTMLInputElement;
                            if (input.files && input.files.length > 0) {
                                this.selectedFile = input.files[0];
                            } else {
                                this.selectedFile = undefined;
                            }
                        }}
                    />
                </div>
                <div class="pf-c-form__group">
                    <label class="pf-c-form__label" for="file-name">
                        <span class="pf-c-form__label-text">${msg("File Name")}</span>
                    </label>
                    <div class="pf-c-form__group-control">
                        <input
                            type="text"
                            class="pf-c-form-control"
                            id="file-name"
                            placeholder=${msg("Leave empty to use original filename")}
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Optionally rename the file (without extension). Leave empty to keep the original filename.",
                            )}
                        </p>
                    </div>
                </div>
            </form>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-file-upload-form": FileUploadForm;
    }
}
