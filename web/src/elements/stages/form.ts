import { customElement, LitElement, CSSResult, property, css } from "lit-element";
import { TemplateResult, html } from "lit-html";
import { Error } from "../../api/Flows";
import { COMMON_STYLES } from "../../common/styles";

@customElement("ak-form-element")
export class FormElement extends LitElement {

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(
            css`
                slot {
                    display: flex;
                    flex-direction: row;
                    align-items: center;
                    justify-content: space-around;
                }
            `
        );
    }

    @property()
    label?: string;

    @property({ type: Boolean })
    required = false;

    @property({ attribute: false })
    errors?: Error[];

    updated(): void {
        this.querySelectorAll<HTMLInputElement>("input[autofocus]").forEach(input => {
            input.focus();
        });
    }

    render(): TemplateResult {
        return html`<div class="pf-c-form__group">
                <label class="pf-c-form__label">
                    <span class="pf-c-form__label-text">${this.label}</span>
                    ${this.required ? html`<span class="pf-c-form__label-required" aria-hidden="true">*</span>` : html``}
                </label>
                <slot></slot>
                ${(this.errors || []).map((error) => {
                        return html`<p class="pf-c-form__helper-text pf-m-error">${error.string}</p>`;
                    })}
            </div>`;
    }

}
