import { Prompt, PromptTypeEnum, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import { first } from "../../../utils";
import { ModelForm } from "../../../elements/forms/ModelForm";

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
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
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
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.required, false)}
                    />
                    <label class="pf-c-check__label"> ${t`Required`} </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Placeholder`} name="placeholder">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.placeholder)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${t`Optionally pre-fill the input value`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Order`} ?required=${true} name="order">
                <input
                    type="number"
                    value="${ifDefined(this.instance?.order)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
        </form>`;
    }
}
