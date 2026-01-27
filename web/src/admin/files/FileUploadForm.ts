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

// Theme variable placeholder for theme-specific files like logo-%(theme)s.png
const THEME_VARIABLE = "%(theme)s";

// Same regex is used in the backend as well (after replacing %(theme)s)
const VALID_FILE_NAME_PATTERN = /^[a-zA-Z0-9._/-]+$/;

// Note: browsers compile `pattern` using the new `v` RegExp flag (Unicode sets). Under `/v`,
// both `/` and `-` must be escaped inside character classes.
// This pattern allows %(theme)s by including %, (, and ) characters
const VALID_FILE_NAME_PATTERN_STRING = "^[a-zA-Z0-9._\\/\\-%()+]+$";

function assertValidFileName(fileName: string): void {
    // Allow %(theme)s placeholder for theme-specific files
    // Replace with placeholder for validation, then check the result
    const nameForValidation = fileName.replaceAll(THEME_VARIABLE, "theme");
    if (!VALID_FILE_NAME_PATTERN.test(nameForValidation)) {
        throw new Error(
            msg(
                "Filename can only contain letters, numbers, dots, hyphens, underscores, slashes, and the placeholder %(theme)s",
            ),
        );
    }
}

function getFileExtension(fileName: string): string {
    const lastDot = fileName.lastIndexOf(".");
    if (lastDot <= 0) return "";
    return fileName.slice(lastDot);
}

function hasBasenameExtension(fileName: string): boolean {
    const baseName = fileName.split("/").pop() ?? fileName;
    const lastDot = baseName.lastIndexOf(".");
    return lastDot > 0;
}

@customElement("ak-file-upload-form")
export class FileUploadForm extends Form<Record<string, unknown>> {
    @property({ type: String, useDefault: true })
    public usage: AdminFileListUsageEnum = AdminFileListUsageEnum.Media;

    @state()
    protected selectedFile: File | null = null;

    #formRef = createRef<HTMLFormElement>();

    public override reset(): void {
        super.reset();

        this.selectedFile = null;
    }

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

        const api = new AdminApi(DEFAULT_CONFIG);
        const customName = typeof data.name === "string" ? data.name.trim() : "";

        // If custom name provided, validate and append original extension
        // Only validate the original filename if no custom name is provided
        let finalName = this.selectedFile.name;
        if (customName) {
            assertValidFileName(customName);
            const ext = getFileExtension(this.selectedFile.name);
            finalName =
                ext && !hasBasenameExtension(customName) ? `${customName}${ext}` : customName;
        } else {
            assertValidFileName(this.selectedFile.name);
        }

        assertValidFileName(finalName);

        await api.adminFileCreate({
            file: this.selectedFile,
            name: finalName,
            usage: this.usage,
        });

        showMessage({
            level: MessageLevel.success,
            message: msg("File uploaded successfully"),
        });

        this.reset();
        this.clearFileInput();
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
                <ak-form-element-horizontal label=${msg("File Name")} name="name">
                    <input
                        type="text"
                        class="pf-c-form-control"
                        pattern=${VALID_FILE_NAME_PATTERN_STRING}
                        placeholder=${msg("Type an optional custom file name...")}
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
