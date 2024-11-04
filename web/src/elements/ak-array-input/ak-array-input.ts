import { AKElement } from "@goauthentik/elements/Base";

import { TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-array-input")
export class AkArrayInput<T> extends AKElement {
    @property()
    elementRenderer: (el: T, idx: number) => TemplateResult = () => {
        return html``;
    };

    @property({ type: Array })
    elements: T[] = [];

    static get styles() {
        return [
            PFBase,
            PFButton,
            PFInputGroup,
            PFFormControl,
            css`
                select.pf-c-form-control {
                    width: 100px;
                }
                .pf-c-input-group {
                    padding-bottom: 8px;
                }
            `,
        ];
    }

    renderButtons(el: T, idx: number) {
        return html`${this.elements.length > 1
            ? html`<button
                  class="pf-c-button pf-m-control"
                  type="button"
                  @click=${() => {
                      const index = this.elements.indexOf(el);
                      if (index > -1) {
                          this.elements.splice(index, 1);
                          this.requestUpdate();
                      }
                  }}
              >
                  <i class="fas fa-minus" aria-hidden="true"></i>
              </button>`
            : nothing}
        ${idx === this.elements.length - 1
            ? html`
                  <button
                      class="pf-c-button pf-m-control"
                      type="button"
                      @click=${() => {
                          this.elements.push({} as unknown as T);
                          this.requestUpdate();
                      }}
                  >
                      <i class="fas fa-plus" aria-hidden="true"></i>
                  </button>
              `
            : nothing} `;
    }

    render() {
        return html`${this.elements.map((el, idx) => {
            return html`<div class="pf-c-input-group">
                ${this.elementRenderer(el, idx)}${this.renderButtons(el, idx)}
            </div>`;
        })}`;
    }
}
