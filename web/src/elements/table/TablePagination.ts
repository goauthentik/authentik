import { AKElement } from "#elements/Base";

import { Pagination } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFPagination from "@patternfly/patternfly/components/Pagination/pagination.css";

export type TablePageChangeListener = (page: number) => void;

@customElement("ak-table-pagination")
export class TablePagination extends AKElement {
    @property({ type: String })
    public label: string | null = null;

    @property({ attribute: false })
    public pages?: Pagination;

    @property({ type: Boolean })
    public loading = false;

    @property({ attribute: false })
    public onPageChange?: TablePageChangeListener;

    static styles: CSSResult[] = [
        PFButton,
        PFPagination,
        css`
            .pf-c-pagination {
                min-width: 8rem;

                &[inert] {
                    opacity: 0.5;
                }
            }
        `,
    ];

    #navigatePrevious = () => {
        this.onPageChange?.(this.pages?.previous || 0);
    };

    #navigateNext = () => {
        this.onPageChange?.(this.pages?.next || 0);
    };

    render() {
        if (!this.pages && !this.loading) {
            return nothing;
        }

        const startIndex = this.pages?.startIndex || 1;
        const endIndex = this.pages?.endIndex || 1;
        const pageCount = this.pages?.count || 1;

        return html` <nav
            aria-label=${msg(str`${this.label || ""} table pagination`)}
            class="pf-c-pagination pf-m-compact pf-m-hidden pf-m-visible-on-md"
            ?inert=${this.loading}
        >
            <div class="pf-c-pagination pf-m-compact pf-m-compact pf-m-hidden pf-m-visible-on-md">
                <div class="pf-c-options-menu">
                    <div class="pf-c-options-menu__toggle pf-m-text pf-m-plain">
                        <span role="heading" aria-level="4" class="pf-c-options-menu__toggle-text">
                            ${msg(str`${startIndex} - ${endIndex} of ${pageCount}`)}
                        </span>
                    </div>
                </div>
                <div class="pf-c-pagination__nav">
                    <div class="pf-c-pagination__nav-control pf-m-prev">
                        <button
                            class="pf-c-button pf-m-plain"
                            @click=${this.#navigatePrevious}
                            ?disabled="${(this.pages?.previous || 0) < 1}"
                            aria-label="${msg("Go to previous page")}"
                        >
                            <i class="fas fa-angle-left" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="pf-c-pagination__nav-control pf-m-next">
                        <button
                            class="pf-c-button pf-m-plain"
                            @click=${this.#navigateNext}
                            ?disabled="${(this.pages?.next || 0) <= 0}"
                            aria-label="${msg("Go to next page")}"
                        >
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </button>
                    </div>
                </div>
            </div>
        </nav>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-table-pagination": TablePagination;
    }
}
