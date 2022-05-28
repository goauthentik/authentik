import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import AKGlobal from "../../../authentik.css";
import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
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

import "../../../elements/Divider";
import "../../../elements/EmptyState";
import "../../../elements/forms/FormElement";
import { LOCALES } from "../../../interfaces/locale";
import { BaseStage } from "../base";

@customElement("ak-stage-prompt")
export class PromptStage extends BaseStage<PromptChallenge, PromptChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFAlert, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal];
    }

    renderPromptInner(prompt: StagePrompt, placeholderAsValue: boolean): string {
        switch (prompt.type) {
            case PromptTypeEnum.Text:
                return `<input
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="off"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${placeholderAsValue ? prompt.placeholder : ""}">`;
            case PromptTypeEnum.TextReadOnly:
                return `<input
                    type="text"
                    name="${prompt.fieldKey}"
                    class="pf-c-form-control"
                    readonly
                    value="${prompt.placeholder}">`;
            case PromptTypeEnum.Username:
                return `<input
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="username"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${placeholderAsValue ? prompt.placeholder : ""}">`;
            case PromptTypeEnum.Email:
                return `<input
                    type="email"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="${placeholderAsValue ? prompt.placeholder : ""}">`;
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
                    ?required=${prompt.required}>`;
            case PromptTypeEnum.Date:
                return `<input
                    type="date"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case PromptTypeEnum.DateTime:
                return `<input
                    type="datetime"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case PromptTypeEnum.Separator:
                return `<ak-divider>${prompt.placeholder}</ak-divider>`;
            case PromptTypeEnum.Hidden:
                return `<input
                    type="hidden"
                    name="${prompt.fieldKey}"
                    value="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case PromptTypeEnum.Static:
                return `<p>${prompt.placeholder}</p>`;
            case PromptTypeEnum.AkLocale:
                return `<select class="pf-c-form-control">
                    <option value="" ${prompt.placeholder === "" ? "selected" : ""}>
                        ${t`Auto-detect (based on your browser)`}
                    </option>
                    ${LOCALES.map((locale) => {
                        return `<option
                            value=${locale.code}
                            ${prompt.placeholder === locale.code ? "selected" : ""}
                        >
                            ${locale.code.toUpperCase()} - ${locale.label}
                        </option>`;
                    }).join("")}
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

    shouldRenderInWrapper(prompt: StagePrompt): bool {
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
                    ?checked=${prompt.placeholder !== ""}
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
                ${unsafeHTML(this.renderPromptInner(prompt, false))}
                ${this.renderPromptHelpText(prompt)}
            </ak-form-element>`;
        }
        return html` ${unsafeHTML(this.renderPromptInner(prompt, false))}
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
