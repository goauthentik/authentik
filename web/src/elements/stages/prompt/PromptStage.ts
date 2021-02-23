import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { Challenge } from "../../../api/Flows";
import { COMMON_STYLES } from "../../../common/styles";
import { BaseStage } from "../base";
import "../form";

export interface Prompt {
    field_key: string;
    label: string;
    type: string;
    required: boolean;
    placeholder: string;
    order: number;
}

export interface PromptChallenge extends Challenge {
    fields: Prompt[];
}

@customElement("ak-stage-prompt")
export class PromptStage extends BaseStage {

    @property({attribute: false})
    challenge?: PromptChallenge;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    renderPromptInner(prompt: Prompt): TemplateResult {
        switch (prompt.type) {
            case "text":
                return html`<input
                    type="text"
                    name="${prompt.field_key}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="off"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="">`;
            case "username":
                return html`<input
                    type="text"
                    name="${prompt.field_key}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="username"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="">`;
            case "email":
                return html`<input
                    type="email"
                    name="${prompt.field_key}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}
                    value="">`;
            case "password":
                return html`<input
                    type="password"
                    name="${prompt.field_key}"
                    placeholder="${prompt.placeholder}"
                    autocomplete="new-password"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "number":
                return html`<input
                    type="number"
                    name="${prompt.field_key}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "checkbox":
                return html`<input
                    type="checkbox"
                    name="${prompt.field_key}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "date":
                return html`<input
                    type="date"
                    name="${prompt.field_key}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "date-time":
                return html`<input
                    type="datetime"
                    name="${prompt.field_key}"
                    placeholder="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "separator":
                return html`<hr>`;
            case "hidden":
                return html`<input
                    type="hidden"
                    name="${prompt.field_key}"
                    value="${prompt.placeholder}"
                    class="pf-c-form-control"
                    ?required=${prompt.required}>`;
            case "static":
                return html`<p
                    class="pf-c-form-control">${prompt.placeholder}
                </p>`;
        }
        return html``;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-loading-state></ak-loading-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" @submit=${(e: Event) => {this.submitForm(e);}}>
                    ${this.challenge.fields.map((prompt) => {
                        return html`<ak-form-element
                            label="${prompt.label}"
                            ?required="${prompt.required}"
                            class="pf-c-form__group"
                            .errors=${(this.challenge?.response_errors || {})[prompt.field_key]}>
                            ${this.renderPromptInner(prompt)}
                        </ak-form-element>`;
                    })}
                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${gettext("Continue")}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                </ul>
            </footer>`;
    }

}
