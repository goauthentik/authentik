import { CURRENT_CLASS, EVENT_REFRESH, ROUTE_SEPARATOR } from "#common/constants";

import { AKElement } from "#elements/Base";
import { getURLParams, updateURLParams } from "#elements/router/RouteMatch";
import { ifPresent } from "#elements/utils/attributes";
import { isFocusable } from "#elements/utils/focus";

import { msg } from "@lit/localize";
import { css, CSSResult, html, LitElement, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFTabs from "@patternfly/patternfly/components/Tabs/tabs.css";
import PFGlobal from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-tabs")
export class Tabs extends AKElement {
    static shadowRootOptions = {
        ...LitElement.shadowRootOptions,
        delegatesFocus: true,
    };

    #focusTargetRef = createRef<HTMLSlotElement>();

    @property()
    pageIdentifier = "page";

    @property()
    currentPage?: string;

    @property({ type: Boolean })
    vertical = false;

    static styles: CSSResult[] = [
        PFGlobal,
        PFTabs,
        css`
            :host([vertical]) {
                display: grid;
                grid-template-columns: auto 1fr;

                .pf-c-tabs {
                    width: auto !important;
                }

                .pf-c-tabs__list {
                    height: 100%;
                }

                .pf-c-tabs .pf-c-tabs__list::before {
                    border-color: transparent;
                }
            }
        `,
    ];

    observer: MutationObserver;

    constructor() {
        super();
        this.observer = new MutationObserver(() => {
            this.requestUpdate();
        });
    }

    connectedCallback(): void {
        super.connectedCallback();
        this.observer.observe(this, {
            attributes: true,
            childList: true,
            subtree: true,
        });

        this.addEventListener("focus", this.#delegateFocusListener);
    }

    disconnectedCallback(): void {
        this.observer.disconnect();
        super.disconnectedCallback();
    }

    onClick(slot?: string): void {
        this.currentPage = slot;
        const params: { [key: string]: string | undefined } = {};
        params[this.pageIdentifier] = slot;
        updateURLParams(params);
        const page = this.querySelector(`[slot='${this.currentPage}']`);
        if (!page) return;

        page.dispatchEvent(new CustomEvent(EVENT_REFRESH));
        page.dispatchEvent(new CustomEvent("activate"));
    }

    #delegateFocusListener = (event: FocusEvent) => {
        const slot = this.#focusTargetRef?.value;

        if (!slot) return;

        const assignedElements = slot.assignedElements({ flatten: true });

        const focusableElement = assignedElements.find(isFocusable);

        // We don't want to refocus if the user is tabbing between elements inside the tabpanel.
        if (focusableElement && event.relatedTarget !== focusableElement) {
            focusableElement.focus({
                preventScroll: true,
            });
        }
    };

    renderTab(page: Element): TemplateResult {
        const slot = page.attributes.getNamedItem("slot")?.value;
        return html` <li class="pf-c-tabs__item ${slot === this.currentPage ? CURRENT_CLASS : ""}">
            <button
                type="button"
                role="tab"
                id=${`${slot}-tab`}
                aria-selected=${slot === this.currentPage ? "true" : "false"}
                aria-controls=${ifPresent(slot)}
                class="pf-c-tabs__link"
                @click=${() => this.onClick(slot)}
            >
                <span class="pf-c-tabs__item-text"> ${page.getAttribute("aria-label")}</span>
            </button>
        </li>`;
    }

    render(): TemplateResult {
        const pages = Array.from(this.querySelectorAll(":scope > [slot^='page-']"));
        if (window.location.hash.includes(ROUTE_SEPARATOR)) {
            const params = getURLParams();
            if (
                this.pageIdentifier in params &&
                !this.currentPage &&
                this.querySelector(`[slot='${params[this.pageIdentifier]}']`) !== null
            ) {
                // To update the URL to match with the current slot
                this.onClick(params[this.pageIdentifier] as string);
            }
        }
        if (!this.currentPage) {
            if (pages.length < 1) {
                return html`<h1>${msg("no tabs defined")}</h1>`;
            }
            const wantedPage = pages[0].attributes.getNamedItem("slot")?.value;
            this.onClick(wantedPage);
        }
        return html`<div class="pf-c-tabs ${this.vertical ? "pf-m-vertical pf-m-box" : ""}">
                <ul
                    class="pf-c-tabs__list"
                    role="tablist"
                    aria-orientation=${this.vertical ? "vertical" : "horizontal"}
                    aria-label=${ifPresent(this.ariaLabel)}
                >
                    ${pages.map((page) => this.renderTab(page))}
                </ul>
            </div>
            <slot name="header"></slot>
            <slot ${ref(this.#focusTargetRef)} name="${ifDefined(this.currentPage)}"></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-tabs": Tabs;
    }
}
