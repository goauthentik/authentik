import "@goauthentik/elements/forms/HorizontalFormElement";
import { PromptStage } from "@goauthentik/flow/stages/prompt/PromptStage";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { PromptTypeEnum, StagePrompt } from "@goauthentik/api";

@customElement("ak-user-stage-prompt")
export class UserSettingsPromptStage extends PromptStage {
    renderPromptInner(prompt: StagePrompt): TemplateResult {
        switch (prompt.type) {
            // Checkbox requires slightly different rendering here due to the use of horizontal form elements
            case PromptTypeEnum.Checkbox:
                return html`<input
                    type="checkbox"
                    class="pf-c-check__input"
                    name="${prompt.fieldKey}"
                    ?checked=${prompt.initialValue !== ""}
                    ?required=${prompt.required}
                    style="vertical-align: bottom"
                />`;
            default:
                return super.renderPromptInner(prompt);
        }
    }

    renderField(prompt: StagePrompt): TemplateResult {
        const errors = (this.challenge?.responseErrors || {})[prompt.fieldKey];
        if (this.shouldRenderInWrapper(prompt)) {
            return html`
                <ak-form-element-horizontal
                    label=${msg(str`${prompt.label}`)}
                    ?required=${prompt.required}
                    name=${prompt.fieldKey}
                    ?invalid=${errors !== undefined}
                    .errorMessages=${(errors || []).map((error) => {
                        return error.string;
                    })}
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
                    ${this.host.tenant?.flowUnenrollment
                        ? html` <a
                              class="pf-c-button pf-m-danger"
                              href="/if/flow/${this.host.tenant.flowUnenrollment}/"
                          >
                              ${msg("Delete account")}
                          </a>`
                        : html``}
                </div>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        return html`<div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
                    ${this.challenge.fields.map((prompt) => {
                        return this.renderField(prompt);
                    })}
                    ${"non_field_errors" in (this.challenge?.responseErrors || {})
                        ? this.renderNonFieldErrors(
                              this.challenge?.responseErrors?.non_field_errors || [],
                          )
                        : html``}
                    ${this.renderContinue()}
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
