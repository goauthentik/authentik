import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Prompt, PromptTypeEnum, StagesApi } from "@goauthentik/api";

@customElement("ak-prompt-form")
export class PromptForm extends ModelForm<Prompt, string> {
    loadInstance(pk: string): Promise<Prompt> {
        return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsRetrieve({
            promptUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated prompt.");
        } else {
            return msg("Successfully created prompt.");
        }
    }

    send = (data: Prompt): Promise<Prompt> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsUpdate({
                promptUuid: this.instance.pk || "",
                promptRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsCreate({
                promptRequest: data,
            });
        }
    };

    renderTypes(): TemplateResult {
        return html`
            <option
                value=${PromptTypeEnum.Text}
                ?selected=${this.instance?.type === PromptTypeEnum.Text}
            >
                ${msg("Text: Simple Text input")}
            </option>
            <option
                value=${PromptTypeEnum.TextReadOnly}
                ?selected=${this.instance?.type === PromptTypeEnum.TextReadOnly}
            >
                ${msg("Text (read-only): Simple Text input, but cannot be edited.")}
            </option>
            <option
                value=${PromptTypeEnum.Username}
                ?selected=${this.instance?.type === PromptTypeEnum.Username}
            >
                ${msg(
                    "Username: Same as Text input, but checks for and prevents duplicate usernames.",
                )}
            </option>
            <option
                value=${PromptTypeEnum.Email}
                ?selected=${this.instance?.type === PromptTypeEnum.Email}
            >
                ${msg("Email: Text field with Email type.")}
            </option>
            <option
                value=${PromptTypeEnum.Password}
                ?selected=${this.instance?.type === PromptTypeEnum.Password}
            >
                ${msg(
                    "Password: Masked input, password is validated against sources. Policies still have to be applied to this Stage. If two of these are used in the same stage, they are ensured to be identical.",
                )}
            </option>
            <option
                value=${PromptTypeEnum.Number}
                ?selected=${this.instance?.type === PromptTypeEnum.Number}
            >
                ${msg("Number")}
            </option>
            <option
                value=${PromptTypeEnum.Checkbox}
                ?selected=${this.instance?.type === PromptTypeEnum.Checkbox}
            >
                ${msg("Checkbox")}
            </option>
            <option
                value=${PromptTypeEnum.Date}
                ?selected=${this.instance?.type === PromptTypeEnum.Date}
            >
                ${msg("Date")}
            </option>
            <option
                value=${PromptTypeEnum.DateTime}
                ?selected=${this.instance?.type === PromptTypeEnum.DateTime}
            >
                ${msg("Date Time")}
            </option>
            <option
                value=${PromptTypeEnum.File}
                ?selected=${this.instance?.type === PromptTypeEnum.File}
            >
                ${msg("File")}
            </option>
            <option
                value=${PromptTypeEnum.Separator}
                ?selected=${this.instance?.type === PromptTypeEnum.Separator}
            >
                ${msg("Separator: Static Separator Line")}
            </option>
            <option
                value=${PromptTypeEnum.Hidden}
                ?selected=${this.instance?.type === PromptTypeEnum.Hidden}
            >
                ${msg("Hidden: Hidden field, can be used to insert data into form.")}
            </option>
            <option
                value=${PromptTypeEnum.Static}
                ?selected=${this.instance?.type === PromptTypeEnum.Static}
            >
                ${msg("Static: Static value, displayed as-is.")}
            </option>
            <option
                value=${PromptTypeEnum.AkLocale}
                ?selected=${this.instance?.type === PromptTypeEnum.AkLocale}
            >
                ${msg("authentik: Locale: Displays a list of locales authentik supports.")}
            </option>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Field Key")} ?required=${true} name="fieldKey">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.fieldKey)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Name of the form field, also used to store the value.")}
                </p>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When used in conjunction with a User Write stage, use attributes.foo to write attributes.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Label")} ?required=${true} name="label">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.label)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Label shown next to/above the prompt.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Type")} ?required=${true} name="type">
                <select class="pf-c-form-control">
                    ${this.renderTypes()}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="required">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.required, false)}
                    />
                    <label class="pf-c-check__label"> ${msg("Required")} </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="placeholderExpression">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.placeholderExpression, false)}
                    />
                    <label class="pf-c-check__label"
                        >${msg("Interpret placeholder as expression")}</label
                    >
                </div>
                <p class="pf-c-form__helper-text">
                    ${msg(`When checked, the placeholder will be evaluated in the same way environment as a property mapping.
                    If the evaluation failed, the placeholder itself is returned.`)}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Placeholder")} name="placeholder">
                <ak-codemirror mode="python" value="${ifDefined(this.instance?.placeholder)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${msg("Optionally pre-fill the input value")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Help text")} name="subText">
                <ak-codemirror mode="htmlmixed" value="${ifDefined(this.instance?.subText)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${msg("Any HTML can be used.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Order")} ?required=${true} name="order">
                <input
                    type="number"
                    value="${first(this.instance?.order, 0)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
        </form>`;
    }
}
