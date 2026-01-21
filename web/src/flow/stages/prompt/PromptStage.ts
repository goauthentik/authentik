import "#elements/Divider";
import "#flow/components/ak-flow-card";

import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { SlottedTemplateResult } from "#elements/types";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { BaseStage } from "#flow/stages/base";
import { LocalePrompt } from "#flow/stages/prompt/components/locale";

import {
    CapabilitiesEnum,
    PromptChallenge,
    PromptChallengeResponseRequest,
    PromptTypeEnum,
    StagePrompt,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCheck from "@patternfly/patternfly/components/Check/check.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

// Fixes horizontal rule <hr> warning in select dropdowns.

/**
 * @prop {PromptChallenge} challenge - The challenge provided to this stage.
 * @prop {StageHost} host - The host managing this stage.
 */
@customElement("ak-stage-prompt")
export class PromptStage extends WithCapabilitiesConfig(
    BaseStage<PromptChallenge, PromptChallengeResponseRequest>,
) {
    static styles: CSSResult[] = [
        PFLogin,
        PFAlert,
        PFForm,
        PFFormControl,
        PFInputGroup,
        PFTitle,
        PFButton,
        PFCheck,
        css`
            textarea {
                min-height: 4em;
                max-height: 15em;
                resize: vertical;
            }
        `,
    ];

    protected renderPromptInner(prompt: StagePrompt): SlottedTemplateResult {
        const fieldId = `field-${prompt.fieldKey}`;

        switch (prompt.type) {
            case PromptTypeEnum.Text:
                return html`<input
                    type="text"
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="off"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.TextArea:
                return html`<textarea
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="off"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                >
${prompt.initialValue}</textarea
                >`;
            case PromptTypeEnum.TextReadOnly:
                return html`<input
                    type="text"
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    readonly
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.TextAreaReadOnly:
                return html`<textarea
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    readonly
                >
${prompt.initialValue}</textarea
                >`;
            case PromptTypeEnum.Username:
                return html`<input
                    type="text"
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="username"
                    spellcheck="false"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.Email:
                return html`<input
                    type="email"
                    id=${fieldId}
                    autocomplete="email"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.Password:
                return html`<input
                    type="password"
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="new-password"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                />`;
            case PromptTypeEnum.Number:
                return html`<input
                    type="number"
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.Date:
                return html`<input
                    type="date"
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.DateTime:
                return html`<input
                    type="datetime"
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.File:
                return html`<input
                    type="file"
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.Separator:
                return html`<ak-divider>${prompt.placeholder}</ak-divider>`;
            case PromptTypeEnum.Hidden:
                return html`<input
                    type="hidden"
                    id=${fieldId}
                    name="${prompt.fieldKey}"
                    value="${prompt.initialValue}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                />`;
            case PromptTypeEnum.Static:
                return html`<p>${unsafeHTML(prompt.initialValue)}</p>`;
            case PromptTypeEnum.Dropdown:
                return html`<select class="pf-c-form-control" name="${prompt.fieldKey}">
                    ${prompt.choices?.map((choice) => {
                        return html`<option
                            value="${choice.value}"
                            ?selected=${prompt.initialValue === choice.value}
                        >
                            ${choice.label}
                        </option>`;
                    })}
                </select>`;
            case PromptTypeEnum.RadioButtonGroup:
                return html`${(prompt.choices || []).map((choice) => {
                    const id = `${prompt.fieldKey}-${choice.value}`;
                    return html`<div class="pf-c-check">
                        <input
                            type="radio"
                            class="pf-c-check__input"
                            name="${prompt.fieldKey}"
                            id="${id}"
                            ?checked="${prompt.initialValue === choice.value}"
                            ?required="${prompt.required}"
                            value="${choice.value}"
                        />
                        <label class="pf-c-check__label" for=${id}>${choice.label}</label>
                    </div> `;
                })}`;
            case PromptTypeEnum.AkLocale: {
                return LocalePrompt({
                    activeLanguageTag: this.activeLanguageTag,
                    prompt,
                    fieldId,
                    debug: this.can(CapabilitiesEnum.CanDebug),
                });
            }
            default:
                return html`<p>invalid type '${prompt.type}'</p>`;
        }
    }

    protected renderPromptHelpText(prompt: StagePrompt) {
        if (!prompt.subText) {
            return nothing;
        }

        return html`<p class="pf-c-form__helper-text">${unsafeHTML(prompt.subText)}</p>`;
    }

    protected shouldRenderInWrapper(prompt: StagePrompt): boolean {
        // Special types that aren't rendered in a wrapper
        return !(
            prompt.type === PromptTypeEnum.Static ||
            prompt.type === PromptTypeEnum.Hidden ||
            prompt.type === PromptTypeEnum.Separator
        );
    }

    protected renderField(prompt: StagePrompt): SlottedTemplateResult {
        // Checkbox is rendered differently
        if (prompt.type === PromptTypeEnum.Checkbox) {
            return html`<div class="pf-c-check">
                <input
                    type="checkbox"
                    class="pf-c-check__input"
                    id="${prompt.fieldKey}"
                    name="${prompt.fieldKey}"
                    ?checked=${prompt.initialValue !== ""}
                    ?required=${prompt.required}
                />
                <label class="pf-c-check__label" for="${prompt.fieldKey}">${prompt.label}</label>
                ${prompt.required
                    ? html`<p class="pf-c-form__helper-text">${msg("Required.")}</p>`
                    : nothing}
                <p class="pf-c-form__helper-text">${unsafeHTML(prompt.subText)}</p>
            </div>`;
        }
        if (this.shouldRenderInWrapper(prompt)) {
            const errors = this.challenge?.responseErrors?.[prompt.fieldKey];

            return html`<div class="pf-c-form__group">
                ${AKLabel(
                    {
                        required: prompt.required,
                        htmlFor: `field-${prompt.fieldKey}`,
                    },
                    prompt.label,
                )}
                ${this.renderPromptInner(prompt)} ${this.renderPromptHelpText(prompt)}
                ${AKFormErrors({ errors })}
            </div>`;
        }
        return html` ${this.renderPromptInner(prompt)} ${this.renderPromptHelpText(prompt)}`;
    }

    protected renderContinue(): SlottedTemplateResult {
        return html`<fieldset class="pf-c-form__group pf-m-action">
            <legend class="sr-only">${msg("Form actions")}</legend>
            <button name="continue" type="submit" class="pf-c-button pf-m-primary pf-m-block">
                ${msg("Continue")}
            </button>
        </fieldset>`;
    }

    protected override render(): SlottedTemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form" @submit=${this.submitForm}>
                ${this.challenge.fields.map((prompt) => {
                    return this.renderField(prompt);
                })}
                ${this.renderNonFieldErrors()} ${this.renderContinue()}
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-prompt": PromptStage;
    }
}
