import "#components/ak-text-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { EmailTemplate, StagesApi } from "@goauthentik/api";

import { ifDefined } from "lit-html/directives/if-defined.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-email-template-form")
export class EmailTemplateForm extends ModelForm<EmailTemplate, string> {
    public static override verboseName = msg("Email Template");
    public static override verboseNamePlural = msg("Email Templates");

    protected loadInstance(pk: string): Promise<EmailTemplate> {
        return aki(StagesApi).stagesEmailTemplatesRetrieve({ uuid: pk });
    }

    public getSuccessMessage(): string | undefined {
        return this.instance
            ? msg("Successfully updated email template.")
            : msg("Successfully created email template.");
    }

    protected async send(data: EmailTemplate): Promise<EmailTemplate> {
        if (this.instance) {
            return aki(StagesApi).stagesEmailTemplatesUpdate({
                uuid: this.instance.uuid,
                emailTemplateRequest: data,
            });
        }

        return aki(StagesApi).stagesEmailTemplatesCreate({
            emailTemplateRequest: data,
        });
    }

    protected override renderForm(): SlottedTemplateResult | null {
        return html`<ak-text-input
                label=${msg("Path")}
                name="path"
                required
                autofocus
                spellcheck="false"
                autocomplete="off"
                value=${ifDefined(this.instance?.path)}
                help=${msg(
                    "Path used to reference this template in `extends` and `include` tags, such as `custom/welcome.html`. The extension is optional.",
                )}
            ></ak-text-input>
            <ak-text-input
                label=${msg("Description")}
                name="description"
                value=${ifDefined(this.instance?.description)}
            ></ak-text-input>
            <ak-form-element-horizontal label=${msg("HTML body")} name="body">
                <ak-codemirror
                    mode="html"
                    raw
                    value=${ifDefined(this.instance?.body)}
                ></ak-codemirror>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Plain text body")} name="bodyPlaintext">
                <ak-codemirror
                    mode="html"
                    raw
                    value=${ifDefined(this.instance?.bodyPlaintext)}
                ></ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Plain text version of the email to be sent alongside HTML. If left empty, emails are sent as HTML only.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-email-template-form": EmailTemplateForm;
    }
}
