import "@goauthentik/elements/Divider";
import "@goauthentik/elements/EmptyState";
import { LOCALES } from "@goauthentik/elements/ak-locale-context/definitions";
import "@goauthentik/elements/forms/FormElement";
import {
    CapabilitiesEnum,
    WithCapabilitiesConfig,
} from "@goauthentik/elements/mixins/capabilities";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCheck from "@patternfly/patternfly/components/Check/check.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    PromptChallenge,
    PromptChallengeResponseRequest,
    PromptTypeEnum,
    StagePrompt,
} from "@goauthentik/api";

@customElement("ak-stage-prompt")
export class PromptStage extends WithCapabilitiesConfig(
    BaseStage<PromptChallenge, PromptChallengeResponseRequest>,
) {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFAlert,
            PFForm,
            PFFormControl,
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
    }

    renderPromptInner(prompt: StagePrompt): TemplateResult {
        switch (prompt.type) {
            case PromptTypeEnum.Text:
                return html`<input
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="off"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.TextArea:
                return html`<textarea
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
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    readonly
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.TextAreaReadOnly:
                return html`<textarea
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
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.Password:
                return html`<input
                    type="password"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="new-password"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                />`;
            case PromptTypeEnum.Number:
                return html`<input
                    type="number"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.Date:
                return html`<input
                    type="date"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.DateTime:
                return html`<input
                    type="datetime"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"
                />`;
            case PromptTypeEnum.File:
                return html`<input
                    type="file"
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
                            value="${choice}"
                            ?selected=${prompt.initialValue === choice}
                        >
                            ${choice}
                        </option>`;
                    })}
                </select>`;
            case PromptTypeEnum.RadioButtonGroup:
                return html`${(prompt.choices || []).map((choice) => {
                    const id = `${prompt.fieldKey}-${choice}`;
                    return html`<div class="pf-c-check">
                        <input
                            type="radio"
                            class="pf-c-check__input"
                            name="${prompt.fieldKey}"
                            id="${id}"
                            ?checked="${prompt.initialValue === choice}"
                            ?required="${prompt.required}"
                            value="${choice}"
                        />
                        <label class="pf-c-check__label" for=${id}>${choice}</label>
                    </div> `;
                })}`;
            case PromptTypeEnum.AkLocale: {
                const locales = this.can(CapabilitiesEnum.CanDebug)
                    ? LOCALES
                    : LOCALES.filter((locale) => locale.code !== "debug");
                const options = locales.map(
                    (locale) =>
                        html`<option
                            value=${locale.code}
                            ?selected=${locale.code === prompt.initialValue}
                        >
                            ${locale.code.toUpperCase()} - ${locale.label()}
                        </option> `,
                );

                return html`<select class="pf-c-form-control" name="${prompt.fieldKey}">
                    <option value="" ?selected=${prompt.initialValue === ""}>
                        ${msg("Auto-detect (based on your browser)")}
                    </option>
                    ${options}
                </select>`;
            }
            default:
                return html`<p>invalid type '${prompt.type}'</p>`;
        }
    }

    renderPromptHelpText(prompt: StagePrompt) {
        if (prompt.subText === "") {
            return nothing;
        }
        return html`<p class="pf-c-form__helper-text">${unsafeHTML(prompt.subText)}</p>`;
    }

    shouldRenderInWrapper(prompt: StagePrompt): boolean {
        // Special types that aren't rendered in a wrapper
        return !(
            prompt.type === PromptTypeEnum.Static ||
            prompt.type === PromptTypeEnum.Hidden ||
            prompt.type === PromptTypeEnum.Separator
        );
    }

    renderField(prompt: StagePrompt): TemplateResult {
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
            return html`<ak-form-element
                label="${prompt.label}"
                ?required="${prompt.required}"
                class="pf-c-form__group"
                .errors=${(this.challenge?.responseErrors || {})[prompt.fieldKey]}
            >
                ${this.renderPromptInner(prompt)} ${this.renderPromptHelpText(prompt)}
            </ak-form-element>`;
        }
        return html` ${this.renderPromptInner(prompt)} ${this.renderPromptHelpText(prompt)}`;
    }

    renderContinue(): TemplateResult {
        return html` <div class="pf-c-form__group pf-m-action">
            <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                ${msg("Continue")}
            </button>
        </div>`;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
                    ${this.challenge.fields.map((prompt) => {
                        return this.renderField(prompt);
                    })}
                    ${this.renderNonFieldErrors()} ${this.renderContinue()}
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-prompt": PromptStage;
    }
}
