import "#elements/forms/HorizontalFormElement";
import "#flow/components/ak-flow-card";

import { globalAK } from "#common/global";
import { autoDetectLanguage, setSessionLocale } from "#common/ui/locale/utils";

import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import { PromptStage } from "#flow/stages/prompt/PromptStage";

import { PromptTypeEnum, StagePrompt } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

/**
 * @prop {StageHost} host - The host managing this stage.
 *
 */
@customElement("ak-user-stage-prompt")
export class UserSettingsPromptStage extends PromptStage {
    protected override renderPromptInner(prompt: StagePrompt): SlottedTemplateResult {
        if (prompt.type === PromptTypeEnum.Checkbox) {
            return html`<input
                type="checkbox"
                class="pf-c-check__input"
                name=${prompt.fieldKey}
                ?checked=${prompt.initialValue !== ""}
                ?required=${prompt.required}
                style="vertical-align: bottom"
            />`;
        }

        return super.renderPromptInner(prompt);
    }

    protected override renderField(prompt: StagePrompt): SlottedTemplateResult {
        const errors = this.challenge?.responseErrors?.[prompt.fieldKey];

        if (this.shouldRenderInWrapper(prompt)) {
            return html`
                <ak-form-element-horizontal
                    ?required=${prompt.required}
                    name=${prompt.fieldKey}
                    .errorMessages=${errors}
                >
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: `field-${prompt.fieldKey}`,
                            required: prompt.required,
                        },
                        prompt.label,
                    )}
                    ${this.renderPromptInner(prompt)} ${this.renderPromptHelpText(prompt)}
                </ak-form-element-horizontal>
            `;
        }
        return html` ${this.renderPromptInner(prompt)} ${this.renderPromptHelpText(prompt)} `;
    }

    protected override renderContinue(): SlottedTemplateResult {
        return html` <div class="pf-c-form__group pf-m-action">
            <div class="pf-c-form__horizontal-group">
                <div class="pf-c-form__actions">
                    <button name="continue" type="submit" class="pf-c-button pf-m-primary">
                        ${msg("Save")}
                    </button>
                    ${this.host.brand?.flowUnenrollment
                        ? html` <a
                              class="pf-c-button pf-m-danger"
                              href="${globalAK().api.base}if/flow/${this.host.brand
                                  .flowUnenrollment}/"
                          >
                              ${msg("Delete account")}
                          </a>`
                        : nothing}
                </div>
            </div>
        </div>`;
    }

    protected override render(): SlottedTemplateResult {
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

    /**
     * Detects if the locale was changed in a prompt stage and updates the session accordingly.
     */
    protected override onSubmitSuccess(payload: Record<string, unknown>): void {
        super.onSubmitSuccess?.(payload);

        if (this.challenge.component !== "ak-stage-prompt") return;

        const localeField = this.challenge.fields.find(
            (field) => field.type === PromptTypeEnum.AkLocale,
        );

        if (!localeField) return;

        const previousLanguageTag = localeField.initialValue;
        const languageTag = localeField?.fieldKey ? payload[localeField.fieldKey] : null;

        if (typeof languageTag !== "string") return;

        // Remove the temporary session locale...
        setSessionLocale(null);

        if (languageTag !== this.activeLanguageTag) {
            this.logger.info("A prompt stage changed the locale", {
                languageTag,
                previousLanguageTag,
            });

            this.activeLanguageTag = autoDetectLanguage(languageTag);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-stage-prompt": UserSettingsPromptStage;
    }
}
