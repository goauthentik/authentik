import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg, str } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import type { BasePagination } from "../types";

const styles = [
    PFBase,
    PFButton,
    PFPagination,
    css`
        @media (prefers-color-scheme: dark) {
            .pf-c-pagination__nav-control .pf-c-button {
                color: var(--pf-c-button--m-plain--disabled--Color);
                --pf-c-button--disabled--Color: var(--pf-c-button--m-plain--Color);
            }
            .pf-c-pagination__nav-control .pf-c-button:disabled {
                color: var(--pf-c-button--disabled--Color);
            }
        }
    `,
];

@customElement("ak-pagination")
export class AkPagination extends CustomEmitterElement(AKElement) {
    static get styles() {
        return styles;
    }

    @property({ attribute: false })
    pages?: BasePagination;

    constructor() {
        super();
        this.onClick = this.onClick.bind(this);
    }

    onClick(nav: number | undefined) {
        this.dispatchCustomEvent("ak-pagination-nav-to", nav ?? 0);
    }

    render() {
        return this.pages
            ? html` <div class="pf-c-pagination pf-m-compact pf-m-hidden pf-m-visible-on-md">
                  <div
                      class="pf-c-pagination pf-m-compact pf-m-compact pf-m-hidden pf-m-visible-on-md"
                  >
                      <div class="pf-c-options-menu">
                          <div class="pf-c-options-menu__toggle pf-m-text pf-m-plain">
                              <span class="pf-c-options-menu__toggle-text">
                                  ${msg(
                                      str`${this.pages?.startIndex} - ${this.pages?.endIndex} of ${this.pages?.count}`,
                                  )}
                              </span>
                          </div>
                      </div>
                      <nav class="pf-c-pagination__nav" aria-label=${msg("Pagination")}>
                          <div class="pf-c-pagination__nav-control pf-m-prev">
                              <button
                                  class="pf-c-button pf-m-plain"
                                  @click=${() => {
                                      this.onClick(this.pages?.previous);
                                  }}
                                  ?disabled="${(this.pages?.previous ?? 0) < 1}"
                                  aria-label="${msg("Go to previous page")}"
                              >
                                  <i class="fas fa-angle-left" aria-hidden="true"></i>
                              </button>
                          </div>
                          <div class="pf-c-pagination__nav-control pf-m-next">
                              <button
                                  class="pf-c-button pf-m-plain"
                                  @click=${() => {
                                      this.onClick(this.pages?.next);
                                  }}
                                  ?disabled="${(this.pages?.next ?? 0) <= 0}"
                                  aria-label="${msg("Go to next page")}"
                              >
                                  <i class="fas fa-angle-right" aria-hidden="true"></i>
                              </button>
                          </div>
                      </nav>
                  </div>
              </div>`
            : nothing;
    }
}

export default AkPagination;

declare global {
    interface HTMLElementTagNameMap {
        "ak-pagination": AkPagination;
    }
}
