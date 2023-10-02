import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

import { ErrorDetail } from "@goauthentik/api";

/**
 * This is used in two places outside of Flow, and in both cases is used primarily to
 * display content, not take input.  It displays the TOPT QR code, and the static
 * recovery tokens.  But it's used a lot in Flow.
 */

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
        return html`<div class="pf-c-form__group">
            <label class="pf-c-form__label">
                <span class="pf-c-form__label-text">${this.label}</span>
                ${this.required
                    ? html`<span class="pf-c-form__label-required" aria-hidden="true">*</span>`
                    : html``}
            </label>
            <slot></slot>
            ${(this.errors || []).map((error) => {
                return html`<p class="pf-c-form__helper-text pf-m-error">${error.string}</p>`;
            })}
        </div>`;
    }
}
