import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import AKGlobal from "../authentik.css";
import PFTabs from "@patternfly/patternfly/components/Tabs/tabs.css";
import PFGlobal from "@patternfly/patternfly/patternfly-base.css";

import { CURRENT_CLASS, EVENT_REFRESH, ROUTE_SEPARATOR } from "../constants";
import { getURLParams, updateURLParams } from "./router/RouteMatch";

@customElement("ak-tabs")
export class Tabs extends LitElement {
    @property()
    pageIdentifier = "page";

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
        const params: { [key: string]: string | undefined } = {};
        params[this.pageIdentifier] = slot;
        updateURLParams(params);
        const page = this.querySelector(`[slot='${this.currentPage}']`);
        if (!page) return;
        page.dispatchEvent(
            new CustomEvent(EVENT_REFRESH, {
                bubbles: true,
                composed: true,
            }),
        );
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
        if (window.location.hash.includes(ROUTE_SEPARATOR)) {
            const params = getURLParams();
            if (this.pageIdentifier in params) {
                if (this.querySelector(`[slot='${params[this.pageIdentifier]}']`) !== null) {
                    // To update the URL to match with the current slot
                    this.currentPage = params[this.pageIdentifier] as string;
                }
            }
        }
        if (!this.currentPage) {
            if (pages.length < 1) {
                return html`<h1>${t`no tabs defined`}</h1>`;
            }
            const wantedPage = pages[0].attributes.getNamedItem("slot")?.value;
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
