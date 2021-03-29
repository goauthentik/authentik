import { customElement, LitElement, CSSResult, property, css } from "lit-element";
import { TemplateResult, html } from "lit-html";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

@customElement("ak-form-element-horizontal")
export class HorizontalFormElement extends LitElement {

    static get styles(): CSSResult[] {
        return [PFForm, PFFormControl, css`
            slot {
                display: flex;
                flex-direction: row;
                align-items: center;
                justify-content: space-around;
            }
            .pf-c-form__group {
                display: grid;
                grid-template-columns: var(--pf-c-form--m-horizontal__group-label--md--GridColumnWidth) var(--pf-c-form--m-horizontal__group-control--md--GridColumnWidth);
            }
            .pf-c-form__group-label {
                padding-top: var(--pf-c-form--m-horizontal__group-label--md--PaddingTop);
            }
        `];
    }

    @property()
    label: string = "";

    @property({ type: Boolean })
    required = false;

    @property()
    errorMessage: string = "";

    @property()
    invalid: boolean = false;

    updated(): void {
        this.querySelectorAll<HTMLInputElement>("input[autofocus]").forEach(input => {
            input.focus();
        });
    }

    render(): TemplateResult {
        return html`<div class="pf-c-form__group">
            <div class="pf-c-form__group-label">
                <label class="pf-c-form__label">
                    <span class="pf-c-form__label-text">${this.label}</span>
                    ${this.required ? html`<span class="pf-c-form__label-required" aria-hidden="true">*</span>` : html``}
                </label>
            </div>
            <div class="pf-c-form__group-control">
                <div class="pf-c-form__horizontal-group">
                    <slot></slot>
                    ${this.invalid ? html`<p class="pf-c-form__helper-text pf-m-error" aria-live="polite">${this.errorMessage}</p>` : html``}
                </div>
            </div>
        </div>`;
    }

}
