import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import AKGlobal from "../authentik.css";
import PFTooltip from "@patternfly/patternfly/components/Tooltip/tooltip.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-tooltip")
export class Tooltip extends LitElement {
    @state()
    open = false;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFTooltip,
            AKGlobal,
            css`
                .pf-c-tooltip__content {
                    text-align: inherit;
                }
                .outer {
                    position: relative;
                }
                .pf-c-tooltip {
                    position: absolute;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<slot
                @mouseenter=${() => {
                    this.open = true;
                }}
                @mouseleave=${() => {
                    this.open = false;
                }}
                name="trigger"
            ></slot>
            ${this.open
                ? html`<div class="outer">
                      <div class="pf-c-tooltip" role="tooltip">
                          <div class="pf-c-tooltip__arrow"></div>

                          <div class="pf-c-tooltip__content">
                              <slot name="tooltip"></slot>
                          </div>
                      </div>
                  </div>`
                : html``}`;
    }
}
