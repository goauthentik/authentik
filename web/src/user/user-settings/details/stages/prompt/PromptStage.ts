import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import { StagePrompt } from "@goauthentik/api";

import "../../../../../elements/forms/HorizontalFormElement";
import { PromptStage } from "../../../../../flows/stages/prompt/PromptStage";

@customElement("ak-user-stage-prompt")
export class UserSettingsPromptStage extends PromptStage {
    renderField(prompt: StagePrompt): TemplateResult {
        const errors = (this.challenge?.responseErrors || {})[prompt.fieldKey];
        return html`
            <ak-form-element-horizontal
                label=${t`${prompt.label}`}
                ?required=${prompt.required}
                name=${prompt.fieldKey}
                ?invalid=${errors !== undefined}
                .errorMessages=${(errors || []).map((error) => {
                    return error.string;
                })}
            >
                ${unsafeHTML(this.renderPromptInner(prompt, true))}
                ${this.renderPromptHelpText(prompt)}
            </ak-form-element-horizontal>
        `;
    }

    renderContinue(): TemplateResult {
        return html` <div class="pf-c-form__group pf-m-action">
            <div class="pf-c-form__horizontal-group">
                <div class="pf-c-form__actions">
                    <button type="submit" class="pf-c-button pf-m-primary">${t`Save`}</button>
                    ${this.host.tenant.flowUnenrollment
                        ? html` <a
                              class="pf-c-button pf-m-danger"
                              href="/if/flow/${this.host.tenant.flowUnenrollment}"
                          >
                              ${t`Delete account`}
                          </a>`
                        : html``}
                </div>
            </div>
        </div>`;
    }
}
