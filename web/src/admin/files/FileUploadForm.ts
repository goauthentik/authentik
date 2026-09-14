import "#elements/forms/HorizontalFormElement";
import "#components/ak-text-input";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";
import { docLink } from "#common/global";

import { Form } from "#elements/forms/Form";
import { PreventFormSubmit } from "#elements/forms/helpers";
import { SlottedTemplateResult } from "#elements/types";
import {
    assertValidFileName,
    FileNamePattern,
    formatValidationMessage,
    getFileExtension,
} from "#elements/utils/files";

import { AKLabel } from "#components/ak-label";

import { AdminApi, AdminFileCreateRequest, UsageEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

interface FileUploadFormData {
    /**
     * Fake path provided by the browser for the selected file.
     */
    file: string;
    /**
     * Custom name for the file, without an extension.
     */
    name: string;
}

@customElement("ak-file-upload-form")
export class FileUploadForm extends Form<FileUploadFormData> {
    public static override verboseName = msg("File");
    public static override verboseNamePlural = msg("Files");
    public static override submitVerb = msg("Upload");
    public static override createLabel = msg("Upload");
    public override headline = msg("Select File");

    public override size = PFSize.Medium;

    @property({ type: String, useDefault: true })
    public usage: UsageEnum = UsageEnum.Media;

    public override async send(data: FileUploadFormData): Promise<AdminFileCreateRequest> {
        const file = this.files<keyof FileUploadFormData>().get("file");

        if (!file) {
            throw new PreventFormSubmit("Selected file not provided", this);
        }

        const customName = typeof data.name === "string" ? data.name.trim() : "";

        // If custom name provided, append original file extension; otherwise use original filename
        const finalName = customName ? `${customName}${getFileExtension(file.name)}` : file.name;

        assertValidFileName(finalName);

        const payload: AdminFileCreateRequest = {
            file,
            name: finalName,
            usage: this.usage,
        };

        return aki(AdminApi)
            .adminFileCreate(payload)
            .then(() => payload);
    }

    protected override renderForm(): SlottedTemplateResult {
        const validationMessage = formatValidationMessage();

        return html`<ak-form-element-horizontal required name="file">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "file-input",
                        required: true,
                    },
                    msg("File"),
                )}
                <input type="file" class="pf-c-form-control" id="file-input" required />
            </ak-form-element-horizontal>
            <ak-text-input
                name="name"
                autocomplete="off"
                control-title=${validationMessage}
                pattern=${FileNamePattern.DOM}
                placeholder=${msg("Type an optional file name without an extension...")}
                label=${msg("Custom Name")}
                .bighelp=${html`<p class="pf-c-form__helper-text">
                    ${msg("Leave empty to keep the original filename.")} ${validationMessage}
                    <a
                        target="_blank"
                        rel="noopener noreferrer"
                        href=${docLink("/customize/file-picker/")}
                    >
                        <br />
                        ${msg("See documentation for path rules and theme-aware names.")}
                    </a>
                </p>`}
            ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-file-upload-form": FileUploadForm;
    }
}
