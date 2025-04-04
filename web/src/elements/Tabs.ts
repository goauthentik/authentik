import { CURRENT_CLASS, EVENT_REFRESH } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import { ROUTE_SEPARATOR } from "@goauthentik/elements/router";
import { getRouteParams, patchRouteParams } from "@goauthentik/elements/router/utils";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFTabs from "@patternfly/patternfly/components/Tabs/tabs.css";
import PFGlobal from "@patternfly/patternfly/patternfly-base.css";

const SLOT_PREFIX = "page-";

@customElement("ak-tabs")
export class Tabs extends AKElement {
    @property()
    pageIdentifier = "page";

    @property()
    currentPage?: string;

    get currentPageParamName(): string | null {
        if (!this.currentPage) return null;

        return this.currentPage.startsWith(SLOT_PREFIX)
            ? this.currentPage.slice(SLOT_PREFIX.length)
            : this.currentPage;
    }

    @property({ type: Boolean })
    vertical = false;

    static get styles(): CSSResult[] {
        return [
            PFGlobal,
            PFTabs,
            css`
                ::slotted(*) {
                    flex-grow: 2;
                }
                :host([vertical]) {
                    display: flex;
                }
                :host([vertical]) .pf-c-tabs {
                    width: auto !important;
                }
                :host([vertical]) .pf-c-tabs__list {
                    height: 100%;
                }
                :host([vertical]) .pf-c-tabs .pf-c-tabs__list::before {
                    border-color: transparent;
                }
            `,
        ];
    }

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
    }

    disconnectedCallback(): void {
        this.observer.disconnect();
        super.disconnectedCallback();
    }

    /**
     * Sync route params with the current page.
     *
     * @todo This should be moved to a router component.
     */
    #syncRouteParams(): void {
        const { currentPageParamName } = this;

        if (!currentPageParamName) return;

        patchRouteParams({
            [this.pageIdentifier]: currentPageParamName,
        });
    }

    activatePage(nextPage?: string): void {
        this.currentPage = nextPage;

        this.#syncRouteParams();

        const page = this.querySelector(`[slot='${this.currentPage}']`);

        if (!page) return;

        page.dispatchEvent(new CustomEvent(EVENT_REFRESH));
        page.dispatchEvent(new CustomEvent("activate"));
    }

    renderTab(page: Element): TemplateResult {
        const slot = page.attributes.getNamedItem("slot")?.value;
        return html` <li class="pf-c-tabs__item ${slot === this.currentPage ? CURRENT_CLASS : ""}">
            <button class="pf-c-tabs__link" @click=${() => this.activatePage(slot)}>
                <span class="pf-c-tabs__item-text"> ${page.getAttribute("data-tab-title")} </span>
            </button>
        </li>`;
    }

    render(): TemplateResult {
        const pages = Array.from(this.querySelectorAll(":scope > [slot^='page-']"));

        if (window.location.hash.includes(ROUTE_SEPARATOR)) {
            const params = getRouteParams();

            const slotName = params[this.pageIdentifier];

            if (
                slotName &&
                typeof slotName === "string" &&
                !this.currentPage &&
                this.querySelector(`[slot='${slotName}']`) !== null
            ) {
                console.debug(
                    `authentik/tabs (${this.pageIdentifier}): setting current page to`,
                    slotName,
                );

                this.activatePage(slotName);
            }
        }

        if (!this.currentPage) {
            if (pages.length < 1) {
                return html`<h1>${msg("no tabs defined")}</h1>`;
            }

            const wantedPage = pages[0].attributes.getNamedItem("slot")?.value;

            console.debug(
                `authentik/tabs (${this.pageIdentifier}): setting current page to`,
                wantedPage,
            );
            this.activatePage(wantedPage);
        }

        return html`<div class="pf-c-tabs ${this.vertical ? "pf-m-vertical pf-m-box" : ""}">
                <ul class="pf-c-tabs__list">
                    ${pages.map((page) => this.renderTab(page))}
                </ul>
            </div>
            <slot name="header"></slot>
            <slot name="${ifDefined(this.currentPage)}"></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-tabs": Tabs;
    }
}
