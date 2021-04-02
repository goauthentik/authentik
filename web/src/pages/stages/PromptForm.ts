import { Prompt, PromptTypeEnum, StagesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-prompt-form")
export class PromptForm extends Form<Prompt> {

    @property({attribute: false})
    prompt?: Prompt;

    getSuccessMessage(): string {
        if (this.prompt) {
            return gettext("Successfully updated prompt.");
        } else {
            return gettext("Successfully created prompt.");
        }
    }

    send = (data: Prompt): Promise<Prompt> => {
        if (this.prompt) {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsUpdate({
                promptUuid: this.prompt.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsCreate({
                data: data
            });
        }
    };

    renderTypes(): TemplateResult {
        return html`
            <option value=${PromptTypeEnum.Text} ?selected=${this.prompt?.type === PromptTypeEnum.Text}>
                ${gettext("Text: Simple Text input")}
            </option>
            <option value=${PromptTypeEnum.Username} ?selected=${this.prompt?.type === PromptTypeEnum.Username}>
                ${gettext("Username: Same as Text input, but checks for and prevents duplicate usernames.")}
            </option>
            <option value=${PromptTypeEnum.Email} ?selected=${this.prompt?.type === PromptTypeEnum.Email}>
                ${gettext("Email: Text field with Email type.")}
            </option>
            <option value=${PromptTypeEnum.Password} ?selected=${this.prompt?.type === PromptTypeEnum.Password}>
                ${gettext("Password: Masked input, password is validated against sources. Policies still have to be applied to this Stage. If two of these are used in the same stage, they are ensured to be identical.")}
            </option>
            <option value=${PromptTypeEnum.Number} ?selected=${this.prompt?.type === PromptTypeEnum.Number}>
                ${gettext("Number")}
            </option>
            <option value=${PromptTypeEnum.Checkbox} ?selected=${this.prompt?.type === PromptTypeEnum.Checkbox}>
                ${gettext("Checkbox")}
            </option>
            <option value=${PromptTypeEnum.Date} ?selected=${this.prompt?.type === PromptTypeEnum.Date}>
                ${gettext("Date")}
            </option>
            <option value=${PromptTypeEnum.DateTime} ?selected=${this.prompt?.type === PromptTypeEnum.DateTime}>
                ${gettext("Date Time")}
            </option>
            <option value=${PromptTypeEnum.Separator} ?selected=${this.prompt?.type === PromptTypeEnum.Separator}>
                ${gettext("Separator: Static Separator Line")}
            </option>
            <option value=${PromptTypeEnum.Hidden} ?selected=${this.prompt?.type === PromptTypeEnum.Hidden}>
                ${gettext("Hidden: Hidden field, can be used to insert data into form.")}
            </option>
            <option value=${PromptTypeEnum.Static} ?selected=${this.prompt?.type === PromptTypeEnum.Static}>
                ${gettext("Static: Static value, displayed as-is.")}
            </option>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Field Key")}
                ?required=${true}
                name="fieldKey">
                <input type="text" value="${ifDefined(this.prompt?.fieldKey)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${gettext("Name of the form field, also used to store the value.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Label")}
                ?required=${true}
                name="label">
                <input type="text" value="${ifDefined(this.prompt?.label)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${gettext("Label shown next to/above the prompt.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Type")}
                ?required=${true}
                name="type">
                <select class="pf-c-form-control">
                    ${this.renderTypes()}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="required">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.prompt?.required || false}>
                    <label class="pf-c-check__label">
                        ${gettext("Required")}
                    </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Placeholder")}
                name="placeholder">
                <input type="text" value="${ifDefined(this.prompt?.placeholder)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${gettext("Optionally pre-fill the input value")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Order")}
                ?required=${true}
                name="order">
                <input type="number" value="${ifDefined(this.prompt?.order)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
        </form>`;
    }

}
