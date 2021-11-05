import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import AKGlobal from "../authentik.css";
import PFTabs from "@patternfly/patternfly/components/Tabs/tabs.css";
import PFGlobal from "@patternfly/patternfly/patternfly-base.css";

import { CURRENT_CLASS, ROUTE_SEPARATOR } from "../constants";

@customElement("ak-tabs")
export class Tabs extends LitElement {
    @property()
    currentPage?: string;

    @property({ type: Boolean })
    vertical = false;

    static get styles(): CSSResult[] {
        return [
            PFGlobal,
            PFTabs,
            AKGlobal,
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

    onClick(slot?: string): void {
        this.currentPage = slot;
        const currentUrl = window.location.hash.slice(1, Infinity).split(ROUTE_SEPARATOR)[0];
        const newUrl = `#${currentUrl};${slot}`;
        history.replaceState(undefined, "", newUrl);
    }

    renderTab(page: Element): TemplateResult {
        const slot = page.attributes.getNamedItem("slot")?.value;
        return html` <li class="pf-c-tabs__item ${slot === this.currentPage ? CURRENT_CLASS : ""}">
            <button class="pf-c-tabs__link" @click=${() => this.onClick(slot)}>
                <span class="pf-c-tabs__item-text"> ${page.getAttribute("data-tab-title")} </span>
            </button>
        </li>`;
    }

    render(): TemplateResult {
        const pages = Array.from(this.querySelectorAll("[slot^='page-']"));
        if (!this.currentPage) {
            if (pages.length < 1) {
                return html`<h1>${t`no tabs defined`}</h1>`;
            }
            let wantedPage = pages[0].attributes.getNamedItem("slot")?.value;
            if (window.location.hash.includes(ROUTE_SEPARATOR)) {
                const urlParts = window.location.hash.slice(1, Infinity).split(ROUTE_SEPARATOR);
                if (this.querySelector(`[slot='${urlParts[1]}']`) !== null) {
                    // To update the URL to match with the current slot
                    wantedPage = urlParts[1];
                }
            }
            this.onClick(wantedPage);
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
