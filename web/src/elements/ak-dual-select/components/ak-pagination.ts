import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg, str } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { BasePagination, DualSelectEventType } from "../types.js";

@customElement("ak-pagination")
export class AkPagination extends CustomEmitterElement<DualSelectEventType>(AKElement) {
    static styles = [
        PFBase,
        PFButton,
        PFPagination,
        css`
            :host([theme="dark"]) {
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

    @property({ attribute: false })
    pages?: BasePagination;

    #clickListener = (nav: number = 0) => {
        this.dispatchCustomEvent(DualSelectEventType.NavigateTo, nav);
    };

    render() {
        const { pages } = this;

        if (!pages) return nothing;

        return html` <div class="pf-c-pagination pf-m-compact pf-m-hidden pf-m-visible-on-md">
            <div class="pf-c-pagination pf-m-compact pf-m-compact pf-m-hidden pf-m-visible-on-md">
                <div class="pf-c-options-menu">
                    <div class="pf-c-options-menu__toggle pf-m-text pf-m-plain">
                        <span class="pf-c-options-menu__toggle-text">
                            ${msg(str`${pages.startIndex} - ${pages.endIndex} of ${pages.count}`)}
                        </span>
                    </div>
                </div>
                <nav class="pf-c-pagination__nav" aria-label=${msg("Pagination")}>
                    <div class="pf-c-pagination__nav-control pf-m-prev">
                        <button
                            class="pf-c-button pf-m-plain"
                            @click=${() => {
                                this.#clickListener(pages.previous);
                            }}
                            ?disabled="${(pages.previous ?? 0) < 1}"
                            aria-label="${msg("Go to previous page")}"
                        >
                            <i class="fas fa-angle-left" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="pf-c-pagination__nav-control pf-m-next">
                        <button
                            class="pf-c-button pf-m-plain"
                            @click=${() => {
                                this.#clickListener(pages.next);
                            }}
                            ?disabled="${(pages.next ?? 0) <= 0}"
                            aria-label="${msg("Go to next page")}"
                        >
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </button>
                    </div>
                </nav>
            </div>
        </div>`;
    }
}

export default AkPagination;

declare global {
    interface HTMLElementTagNameMap {
        "ak-pagination": AkPagination;
    }
}
