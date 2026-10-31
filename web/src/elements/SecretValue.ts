import "#components/ak-hidden-text-input";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

import { AKElement } from "#elements/Base";
import { IconCopyButton } from "#elements/buttons/IconCopyButton";

import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-secret-value")
export class SecretValue extends AKElement {
    public static styles = [
        PFButton,
        PFForm,
        PFFormControl,
        PFInputGroup,
        css`
            :host {
                display: block;
            }
            textarea {
                resize: vertical;
            }
        `,
    ];

    @property()
    public value = "";

    @property()
    public label = "";

    @property({ type: Boolean })
    public multiline = false;

    protected override render() {
        return this.multiline
            ? html`<div class="pf-c-input-group">
                  <textarea
                      class="pf-c-form-control pf-m-monospace"
                      aria-label=${this.label}
                      rows="4"
                      readonly
                      spellcheck="false"
                      .value=${this.value}
                  ></textarea>
                  ${IconCopyButton({ source: this.value, entityLabel: this.label })}
              </div>`
            : html`<ak-hidden-text-input
                  .label=${this.label}
                  .value=${this.value}
                  readonly
                  copyable
                  input-hint="code"
              ></ak-hidden-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-secret-value": SecretValue;
    }
}
