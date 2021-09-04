import { t } from "@lingui/macro";
import { CSSResult, customElement, html, TemplateResult } from "lit-element";
import { unsafeHTML } from "lit-html/directives/unsafe-html";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import AKGlobal from "../../../authentik.css";
import { BaseStage } from "../base";
import "../../../elements/forms/FormElement";
import "../../../elements/EmptyState";
import "../../../elements/Divider";
import { PromptChallenge, PromptChallengeResponseRequest, StagePrompt } from "@goauthentik/api";

@customElement("ak-stage-prompt")
export class PromptStage extends BaseStage<PromptChallenge, PromptChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFAlert, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal];
    }

    renderPromptInner(prompt: StagePrompt): string {
        switch (prompt.type) {
            case "text":
                return `<input
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="off"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="">`;
            case "username":
                return `<input
                    type="text"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="username"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="">`;
            case "email":
                return `<input
                    type="email"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="">`;
            case "password":
                return `<input
                    type="password"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="new-password"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "number":
                return `<input
                    type="number"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "date":
                return `<input
                    type="date"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "date-time":
                return `<input
                    type="datetime"
                    name="${prompt.fieldKey}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "separator":
                return `<ak-divider>${prompt.placeholder}</ak-divider>`;
            case "hidden":
                return `<input
                    type="hidden"
                    name="${prompt.fieldKey}"
                    value="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "static":
                return `<p>${prompt.placeholder}</p>`;
        }
        return "";
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
                        // Checkbox is rendered differently
                        if (prompt.type === "checkbox") {
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
                            </div>`;
                        }
                        // Special types that aren't rendered in a wrapper
                        if (
                            prompt.type === "static" ||
                            prompt.type === "hidden" ||
                            prompt.type === "separator"
                        ) {
                            return unsafeHTML(this.renderPromptInner(prompt));
                        }
                        return html`<ak-form-element
                            label="${prompt.label}"
                            ?required="${prompt.required}"
                            class="pf-c-form__group"
                            .errors=${(this.challenge?.responseErrors || {})[prompt.fieldKey]}
                        >
                            ${unsafeHTML(this.renderPromptInner(prompt))}
                        </ak-form-element>`;
                    })}
                    ${"non_field_errors" in (this.challenge?.responseErrors || {})
                        ? this.renderNonFieldErrors(
                              this.challenge?.responseErrors?.non_field_errors || [],
                          )
                        : html``}
                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${t`Continue`}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
