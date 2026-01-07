import "#elements/forms/HorizontalFormElement";
import "#flow/components/ak-flow-card";

import { DEFAULT_CONFIG } from "#common/api/config";
import { globalAK } from "#common/global";
import { autoDetectLanguage, setSessionLocale } from "#common/ui/locale/utils";

import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import { PromptStage } from "#flow/stages/prompt/PromptStage";

import { AdminApi, PromptTypeEnum, Settings, StagePrompt } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-user-stage-prompt")
export class UserSettingsPromptStage extends PromptStage {
    @state()
    private settings?: Settings;

    constructor() {
        super();
        new AdminApi(DEFAULT_CONFIG).adminSettingsRetrieve().then((settings) => {
            this.settings = settings;
        });
    }

    isFieldReadOnly(prompt: StagePrompt): boolean {
        if (
            prompt.type === PromptTypeEnum.Email &&
            this.settings?.defaultUserChangeEmail === false
        ) {
            return true;
        }
        if (
            prompt.type === PromptTypeEnum.Username &&
            this.settings?.defaultUserChangeUsername === false
        ) {
            return true;
        }
        if (
            prompt.type === PromptTypeEnum.Text &&
            prompt.fieldKey === "name" &&
            this.settings?.defaultUserChangeName === false
        ) {
            return true;
        }
        return false;
    }

    renderPromptHelpText(prompt: StagePrompt) {
        if (this.isFieldReadOnly(prompt)) {
            return html`<p class="pf-c-form__helper-text">
                ${msg("Not allowed to change this field. Please contact your administrator.")}
            </p>`;
        }
        return super.renderPromptHelpText(prompt);
    }

    renderPromptInner(prompt: StagePrompt): SlottedTemplateResult {
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

        const disabled = this.isFieldReadOnly(prompt);
        return super.renderPromptInner(prompt, disabled);
    }

    renderField(prompt: StagePrompt): TemplateResult {
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

    renderContinue(): TemplateResult {
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
