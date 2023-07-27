import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

import { ErrorDetail } from "@goauthentik/api";

@customElement("ak-form-element")
export class FormElement extends AKElement {
    static get styles(): CSSResult[] {
        return [PFForm, PFFormControl];
    }

    @property()
    label?: string;

    @property({ type: Boolean })
    required = false;

    @property({ attribute: false })
    errors?: ErrorDetail[];

    updated(): void {
        this.querySelectorAll<HTMLInputElement>("input[autofocus]").forEach((input) => {
            input.focus();
        });
    }

    render(): TemplateResult {
        return html`<div class="pf-v5-c-form__group">
            <label class="pf-v5-c-form__label">
                <span class="pf-v5-c-form__label-text">${this.label}</span>
                ${this.required
                    ? html`<span class="pf-v5-c-form__label-required" aria-hidden="true">*</span>`
                    : html``}
            </label>
            <slot></slot>
            ${(this.errors || []).map((error) => {
                return html`<p class="pf-v5-c-form__helper-text pf-m-error">${error.string}</p>`;
            })}
        </div>`;
    }
}
