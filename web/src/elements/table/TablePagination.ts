import { AKElement } from "@goauthentik/elements/Base";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Pagination } from "@goauthentik/api";

@customElement("ak-table-pagination")
export class TablePagination extends AKElement {
    @property({ attribute: false })
    pages?: Pagination;

    @property({ attribute: false })
    pageChangeHandler: (page: number) => void = () => {
        return;
    };

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFPagination,
            css`
                :host([theme="dark"]) .pf-c-pagination__nav-control .pf-c-button {
                    color: var(--pf-c-button--m-plain--disabled--Color);
                    --pf-c-button--disabled--Color: var(--pf-c-button--m-plain--Color);
                }
                :host([theme="dark"]) .pf-c-pagination__nav-control .pf-c-button:disabled {
                    color: var(--pf-c-button--disabled--Color);
                }
            `,
        ];
    }

    render(): TemplateResult {
        if (!this.pages) {
            return html``;
        }
        return html` <div class="pf-c-pagination pf-m-compact pf-m-hidden pf-m-visible-on-md">
            <div class="pf-c-pagination pf-m-compact pf-m-compact pf-m-hidden pf-m-visible-on-md">
                <div class="pf-c-options-menu">
                    <div class="pf-c-options-menu__toggle pf-m-text pf-m-plain">
                        <span class="pf-c-options-menu__toggle-text">
                            ${msg(
                                str`${this.pages?.startIndex} - ${this.pages?.endIndex} of ${this.pages?.count}`,
                            )}
                        </span>
                    </div>
                </div>
                <nav class="pf-c-pagination__nav" aria-label="Pagination">
                    <div class="pf-c-pagination__nav-control pf-m-prev">
                        <button
                            class="pf-c-button pf-m-plain"
                            @click=${() => {
                                this.pageChangeHandler(this.pages?.previous || 0);
                            }}
                            ?disabled="${(this.pages?.previous || 0) < 1}"
                            aria-label="${msg("Go to previous page")}"
                        >
                            <i class="fas fa-angle-left" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="pf-c-pagination__nav-control pf-m-next">
                        <button
                            class="pf-c-button pf-m-plain"
                            @click=${() => {
                                this.pageChangeHandler(this.pages?.next || 0);
                            }}
                            ?disabled="${(this.pages?.next || 0) <= 0}"
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
