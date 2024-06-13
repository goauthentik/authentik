import { AKElement } from "@goauthentik/elements/Base";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * Form Group
 *
 * Mostly visual effects, with a single interaction for opening/closing the view.
 *
 */

/**
 * TODO: Listen for custom events from its children about 'invalidation' events, and
 * trigger the `expanded` property as needed.
 */

@customElement("ak-form-group")
export class FormGroup extends AKElement {
    @property({ type: Boolean, reflect: true })
    expanded = false;

    @property({ type: String, attribute: "aria-label", reflect: true })
    ariaLabel = "Details";

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFForm,
            PFButton,
            PFFormControl,
            css`
                slot[name="body"][hidden] {
                    display: none !important;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<div class="pf-c-form__field-group ${this.expanded ? "pf-m-expanded" : ""}">
            <div class="pf-c-form__field-group-toggle">
                <div class="pf-c-form__field-group-toggle-button">
                    <button
                        class="pf-c-button pf-m-plain"
                        type="button"
                        aria-expanded="${this.expanded}"
                        aria-label=${this.ariaLabel}
                        @click=${() => {
                            this.expanded = !this.expanded;
                        }}
                    >
                        <span class="pf-c-form__field-group-toggle-icon">
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </span>
                    </button>
                </div>
            </div>
            <div class="pf-c-form__field-group-header">
                <div class="pf-c-form__field-group-header-main">
                    <div class="pf-c-form__field-group-header-title">
                        <div class="pf-c-form__field-group-header-title-text">
                            <slot name="header"></slot>
                        </div>
                    </div>
                    <div class="pf-c-form__field-group-header-description">
                        <slot name="description"></slot>
                    </div>
                </div>
            </div>
            <slot ?hidden=${!this.expanded} class="pf-c-form__field-group-body" name="body"></slot>
        </div>`;
    }
}
