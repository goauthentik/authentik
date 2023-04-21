import { LOCALES } from "@goauthentik/common/ui/locale";
import { rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Divider";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    CapabilitiesEnum,
    PromptChallenge,
    PromptChallengeResponseRequest,
    PromptTypeEnum,
    StagePrompt,
} from "@goauthentik/api";

@customElement("ak-stage-prompt")
export class PromptStage extends BaseStage<PromptChallenge, PromptChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFAlert,
            PFForm,
            PFFormControl,
            PFTitle,
            PFButton,
            css`
                textarea {
                    min-height: 4em;
                    max-height: 15em;
                    resize: vertical;
                }
            `,
        ];
    }

    renderPromptInner(prompt: StagePrompt): string {
        switch (prompt.type) {
            case PromptTypeEnum.Text:
                return `<input
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="off"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}">`;
            case PromptTypeEnum.TextArea:
                return `<textarea
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="off"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}"">`;
            case PromptTypeEnum.TextReadOnly:
                return `<input
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    readonly
                    value="${prompt.initialValue}">`;
            case PromptTypeEnum.TextAreaReadOnly:
                return `<textarea
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    readonly
                    value="${prompt.initialValue}">`;
            case PromptTypeEnum.Username:
                return `<input
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="username"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}">`;
            case PromptTypeEnum.Email:
                return `<input
                    type="email"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}">`;
            case PromptTypeEnum.Password:
                return `<input
                    type="password"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="new-password"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case PromptTypeEnum.Number:
                return `<input
                    type="number"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}">`;
            case PromptTypeEnum.Date:
                return `<input
                    type="date"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}">`;
            case PromptTypeEnum.DateTime:
                return `<input
                    type="datetime"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}">`;
            case PromptTypeEnum.File:
                return `<input
                    type="file"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${prompt.initialValue}">`;
            case PromptTypeEnum.Separator:
                return `<ak-divider>${prompt.placeholder}</ak-divider>`;
            case PromptTypeEnum.Hidden:
                return `<input
                    type="hidden"
                    name="${prompt.fieldKey}"
                    value="${prompt.initialValue}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case PromptTypeEnum.Static:
                return `<p>${prompt.initialValue}</p>`;
            case PromptTypeEnum.Dropdown:
                return `<select class="pf-c-form-control" name="${prompt.fieldKey}">
                    ${prompt.choices
                        ?.map((choice) => {
                            return `<option
                            value="${choice}"
                            ?selected=${prompt.initialValue === choice}
                        >
                            ${choice}
                        </option>`;
                        })
                        .join("")}
                </select>`;
            case PromptTypeEnum.RadioButtonGroup:
                return (
                    prompt.choices
                        ?.map((choice) => {
                            return ` <div class="pf-c-check">
                                    <input
                                        type="radio"
                                        class="pf-c-check__input"
                                        name="${prompt.fieldKey}"
                                        checked="${prompt.initialValue === choice}"
                                        required="${prompt.required}"
                                        value="${choice}"
                                    />
                                    <label class="pf-c-check__label">${choice}</label>
                                </div>
                            `;
                        })
                        .join("") || ""
                );
            case PromptTypeEnum.AkLocale:
                return `<select class="pf-c-form-control" name="${prompt.fieldKey}">
                    <option value="" ${prompt.initialValue === "" ? "selected" : ""}>
                        ${t`Auto-detect (based on your browser)`}
                    </option>
                    ${LOCALES.filter((locale) => {
                        // Only show debug locale if debug mode is enabled
                        if (locale.code === "debug") {
                            return rootInterface()?.config?.capabilities.includes(
                                CapabilitiesEnum.CanDebug,
                            );
                        }
                        return true;
                    })
                        .map((locale) => {
                            return `<option
                            value=${locale.code}
                            ${prompt.initialValue === locale.code ? "selected" : ""}
                        >
                            ${locale.code.toUpperCase()} - ${locale.label}
                        </option>`;
                        })
                        .join("")}
                </select>`;
            default:
                return `<p>invalid type '${prompt.type}'</p>`;
        }
    }

    renderPromptHelpText(prompt: StagePrompt): TemplateResult {
        if (prompt.subText === "") {
            return html``;
        }
        return html`<p class="pf-c-form__helper-text">${unsafeHTML(prompt.subText)}</p>`;
    }

    shouldRenderInWrapper(prompt: StagePrompt): boolean {
        // Special types that aren't rendered in a wrapper
        if (
            prompt.type === PromptTypeEnum.Static ||
            prompt.type === PromptTypeEnum.Hidden ||
            prompt.type === PromptTypeEnum.Separator
        ) {
            return false;
        }
        return true;
    }

    renderField(prompt: StagePrompt): TemplateResult {
        // Checkbox is rendered differently
        if (prompt.type === PromptTypeEnum.Checkbox) {
            return html`<div class="pf-c-check">
                <input
                    type="checkbox"
                    class="pf-c-check__input"
                    name="${prompt.fieldKey}"
                    ?checked=${prompt.initialValue !== ""}
                    ?required=${prompt.required}
                />
                <label class="pf-c-check__label">${prompt.label}</label>
                ${prompt.required
                    ? html`<p class="pf-c-form__helper-text">${t`Required.`}</p>`
                    : html``}
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
                ${unsafeHTML(this.renderPromptInner(prompt))} ${this.renderPromptHelpText(prompt)}
            </ak-form-element>`;
        }
        return html` ${unsafeHTML(this.renderPromptInner(prompt))}
        ${this.renderPromptHelpText(prompt)}`;
    }

    renderContinue(): TemplateResult {
        return html` <div class="pf-c-form__group pf-m-action">
            <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                ${t`Continue`}
            </button>
        </div>`;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
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
