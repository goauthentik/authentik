import { AKElement } from "@goauthentik/elements/Base";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFChip from "@patternfly/patternfly/components/Chip/chip.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-chip")
export class Chip extends AKElement {
    @property()
    value?: number | string;

    @property({ type: Boolean })
    removable = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFChip];
    }

    render(): TemplateResult {
        return html`<li class="pf-c-chip-group__list-item">
            <div class="pf-c-chip">
                <span class="pf-c-chip__text">
                    <slot></slot>
                </span>
                ${this.removable
                    ? html`<button
                          class="pf-c-button pf-m-plain"
                          type="button"
                          @click=${() => {
                              this.dispatchEvent(
                                  new CustomEvent("remove", {
                                      bubbles: true,
                                      composed: true,
                                  }),
                              );
                          }}
                      >
                          <pf-tooltip position="top" content=${msg("Remove item")}>
                              <i class="fas fa-times" aria-hidden="true"></i>
                          </pf-tooltip>
                      </button>`
                    : html``}
            </div>
        </li>`;
    }
}
