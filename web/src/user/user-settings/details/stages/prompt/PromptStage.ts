import "#elements/forms/HorizontalFormElement";
import "#flow/components/ak-flow-card";

import { globalAK } from "#common/global";

import { PromptStage } from "#flow/stages/prompt/PromptStage";

import { PromptTypeEnum, StagePrompt } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-stage-prompt")
export class UserSettingsPromptStage extends PromptStage {
    renderPromptInner(prompt: StagePrompt): TemplateResult {
        return prompt.type === PromptTypeEnum.Checkbox
            ? html`<input
                  type="checkbox"
                  class="pf-c-check__input"
                  name="${prompt.fieldKey}"
                  ?checked=${prompt.initialValue !== ""}
                  ?required=${prompt.required}
                  style="vertical-align: bottom"
              />`
            : super.renderPromptInner(prompt);
    }

    renderField(prompt: StagePrompt): TemplateResult {
        const errors = this.challenge?.responseErrors?.[prompt.fieldKey];

        if (this.shouldRenderInWrapper(prompt)) {
            return html`
                <ak-form-element-horizontal
                    label=${msg(str`${prompt.label}`)}
                    ?required=${prompt.required}
                    name=${prompt.fieldKey}
                    ?invalid=${!!errors}
                    .errorMessages=${errors}
                >
                    ${this.renderPromptInner(prompt)} ${this.renderPromptHelpText(prompt)}
                </ak-form-element-horizontal>
            `;
        }
        return html` ${this.renderPromptInner(prompt)} ${this.renderPromptHelpText(prompt)} `;
    }

    renderContinue(): TemplateResult {
        return html` <div class="pf-c-form__group pf-m-action">
            <div class="pf-c-form__horizontal-group">
                <div class="pf-c-form__actions">
                    <button type="submit" class="pf-c-button pf-m-primary">${msg("Save")}</button>
                    ${this.host.brand?.flowUnenrollment
                        ? html` <a
                              class="pf-c-button pf-m-danger"
                              href="${globalAK().api.base}if/flow/${this.host.brand
                                  .flowUnenrollment}/"
                          >
                              ${msg("Delete account")}
                          </a>`
                        : html``}
                </div>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
                <form
                    class="pf-c-form"
                    @submit=${this.submitForm}
                >
                    ${this.challenge.fields.map((prompt) => {
                        return this.renderField(prompt);
                    })}
                    ${this.renderNonFieldErrors()} ${this.renderContinue()}
                </form>
            </div>
            </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-stage-prompt": UserSettingsPromptStage;
    }
}
