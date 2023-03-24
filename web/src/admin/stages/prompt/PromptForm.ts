import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

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
            return t`Successfully updated prompt.`;
        } else {
            return t`Successfully created prompt.`;
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
                ${t`Text: Simple Text input`}
            </option>
            <option
                value=${PromptTypeEnum.TextArea}
                ?selected=${this.instance?.type === PromptTypeEnum.TextArea}
            >
                ${t`Text Area: Multiline text input`}
            </option>
            <option
                value=${PromptTypeEnum.TextReadOnly}
                ?selected=${this.instance?.type === PromptTypeEnum.TextReadOnly}
            >
                ${t`Text (read-only): Simple Text input, but cannot be edited.`}
            </option>
            <option
                value=${PromptTypeEnum.TextAreaReadOnly}
                ?selected=${this.instance?.type === PromptTypeEnum.TextAreaReadOnly}
            >
                ${t`Text Area (read-only): Multiline text input, but cannot be edited.`}
            </option>
            <option
                value=${PromptTypeEnum.Username}
                ?selected=${this.instance?.type === PromptTypeEnum.Username}
            >
                ${t`Username: Same as Text input, but checks for and prevents duplicate usernames.`}
            </option>
            <option
                value=${PromptTypeEnum.Email}
                ?selected=${this.instance?.type === PromptTypeEnum.Email}
            >
                ${t`Email: Text field with Email type.`}
            </option>
            <option
                value=${PromptTypeEnum.Password}
                ?selected=${this.instance?.type === PromptTypeEnum.Password}
            >
                ${t`Password: Masked input, password is validated against sources. Policies still have to be applied to this Stage. If two of these are used in the same stage, they are ensured to be identical.`}
            </option>
            <option
                value=${PromptTypeEnum.Number}
                ?selected=${this.instance?.type === PromptTypeEnum.Number}
            >
                ${t`Number`}
            </option>
            <option
                value=${PromptTypeEnum.Checkbox}
                ?selected=${this.instance?.type === PromptTypeEnum.Checkbox}
            >
                ${t`Checkbox`}
            </option>
            <option
                value=${PromptTypeEnum.RadioButtonGroup}
                ?selected=${this.instance?.type === PromptTypeEnum.RadioButtonGroup}
            >
                ${t`Radio Button Group (fixed choice)`}
            </option>
            <option
                value=${PromptTypeEnum.Dropdown}
                ?selected=${this.instance?.type === PromptTypeEnum.Dropdown}
            >
                ${t`Dropdown (fixed choice)`}
            </option>
            <option
                value=${PromptTypeEnum.Date}
                ?selected=${this.instance?.type === PromptTypeEnum.Date}
            >
                ${t`Date`}
            </option>
            <option
                value=${PromptTypeEnum.DateTime}
                ?selected=${this.instance?.type === PromptTypeEnum.DateTime}
            >
                ${t`Date Time`}
            </option>
            <option
                value=${PromptTypeEnum.File}
                ?selected=${this.instance?.type === PromptTypeEnum.File}
            >
                ${t`File`}
            </option>
            <option
                value=${PromptTypeEnum.Separator}
                ?selected=${this.instance?.type === PromptTypeEnum.Separator}
            >
                ${t`Separator: Static Separator Line`}
            </option>
            <option
                value=${PromptTypeEnum.Hidden}
                ?selected=${this.instance?.type === PromptTypeEnum.Hidden}
            >
                ${t`Hidden: Hidden field, can be used to insert data into form.`}
            </option>
            <option
                value=${PromptTypeEnum.Static}
                ?selected=${this.instance?.type === PromptTypeEnum.Static}
            >
                ${t`Static: Static value, displayed as-is.`}
            </option>
            <option
                value=${PromptTypeEnum.AkLocale}
                ?selected=${this.instance?.type === PromptTypeEnum.AkLocale}
            >
                ${t`authentik: Locale: Displays a list of locales authentik supports.`}
            </option>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Unique name of this field, used for selecting fields in prompt stages.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Field Key`} ?required=${true} name="fieldKey">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.fieldKey)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Name of the form field, also used to store the value.`}
                </p>
                <p class="pf-c-form__helper-text">
                    ${t`When used in conjunction with a User Write stage, use attributes.foo to write attributes.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Label`} ?required=${true} name="label">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.label)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${t`Label shown next to/above the prompt.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Type`} ?required=${true} name="type">
                <select class="pf-c-form-control">
                    ${this.renderTypes()}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="required">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.required, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${t`Required`}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="placeholderExpression">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.placeholderExpression, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label"
                        >${t`Interpret placeholder as expression`}</span
                    >
                </label>
                <p class="pf-c-form__helper-text">
                    ${t`When checked, the placeholder will be evaluated in the same way a property mapping is.
                    If the evaluation fails, the placeholder itself is returned.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Placeholder`} name="placeholder">
                <ak-codemirror mode="python" value="${ifDefined(this.instance?.placeholder)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${t`Optionally provide a short hint that describes the expected input value.
                    When creating a fixed choice field, enable interpreting as
                    expression and return a list to return multiple choices.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="initialValueExpression">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.initialValueExpression, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label"
                        >${t`Interpret initial value as expression`}</span
                    >
                </label>
                <p class="pf-c-form__helper-text">
                    ${t`When checked, the initial value will be evaluated in the same way a property mapping is.
                    If the evaluation fails, the initial value itself is returned.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Initial value`} name="initialValue">
                <ak-codemirror mode="python" value="${ifDefined(this.instance?.initialValue)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${t`Optionally pre-fill the input with an initial value.
                    When creating a fixed choice field, enable interpreting as
                    expression and return a list to return multiple default choices.`}}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Help text`} name="subText">
                <ak-codemirror mode="htmlmixed" value="${ifDefined(this.instance?.subText)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${t`Any HTML can be used.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Order`} ?required=${true} name="order">
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
