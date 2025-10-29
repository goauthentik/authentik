import { CURRENT_CLASS, EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import { getURLParams, updateURLParams } from "#elements/router/RouteMatch";
import { ifPresent } from "#elements/utils/attributes";
import { isFocusable } from "#elements/utils/focus";

import { msg } from "@lit/localize";
import { css, CSSResult, html, LitElement, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFTabs from "@patternfly/patternfly/components/Tabs/tabs.css";
import PFGlobal from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-tabs")
export class Tabs extends AKElement {
    static shadowRootOptions = {
        ...LitElement.shadowRootOptions,
        delegatesFocus: true,
    };
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

    @property({ type: String })
    public pageIdentifier = "page";

    @property({ type: Boolean, useDefault: true })
    public vertical = false;

    @state()
    protected activeTabName: string | null = null;

    @state()
    protected tabs: ReadonlyMap<string, Element> = new Map();

    #focusTargetRef = createRef<HTMLSlotElement>();
    #observer: MutationObserver | null = null;

    #updateTabs = (): void => {
        this.tabs = new Map(
            Array.from(this.querySelectorAll(":scope > [slot^='page-']"), (element) => {
                return [element.getAttribute("slot") || "", element];
            }),
        );
    };

    public override connectedCallback(): void {
        super.connectedCallback();

        this.#observer = new MutationObserver(this.#updateTabs);

        this.addEventListener("focus", this.#delegateFocusListener);

        if (!this.activeTabName) {
            const params = getURLParams();
            const tabParam = params[this.pageIdentifier];

            if (
                tabParam &&
                typeof tabParam === "string" &&
                this.querySelector(`[slot='${tabParam}']`)
            ) {
                this.activeTabName = tabParam;
            } else {
                this.#updateTabs();
                this.activeTabName = this.tabs.keys().next().value || null;
            }
        }
    }

    public override firstUpdated(): void {
        this.#observer?.observe(this, {
            attributes: true,
            childList: true,
            subtree: true,
        });
    }

    public override disconnectedCallback(): void {
        this.#observer?.disconnect();
        super.disconnectedCallback();
    }

    public activateTab(nextTabName: string): void {
        if (!nextTabName) {
            console.warn("Cannot activate falsey tab name:", nextTabName);
            return;
        }

        if (!this.tabs.has(nextTabName)) {
            console.warn("Cannot activate unknown tab name:", nextTabName, this.tabs);
            return;
        }

        const firstTab = this.tabs.keys().next().value || null;

        // We avoid adding the tab parameter to the URL if it's the first tab
        // to both reduce URL length and ensure that tests do not have to deal with
        // unnecessary URL parameters.

        updateURLParams({
            [this.pageIdentifier]: nextTabName === firstTab ? null : nextTabName,
        });

        this.activeTabName = nextTabName;

        const page = this.querySelector(`[slot='${this.activeTabName}']`);
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

    renderTab(slotName: string, tabPanel: Element): TemplateResult {
        return html` <li
            class="pf-c-tabs__item ${slotName === this.activeTabName ? CURRENT_CLASS : ""}"
        >
            <button
                type="button"
                role="tab"
                id=${`${slotName}-tab`}
                aria-selected=${slotName === this.activeTabName ? "true" : "false"}
                aria-controls=${ifPresent(slotName)}
                class="pf-c-tabs__link"
                @click=${() => this.activateTab(slotName)}
            >
                <span class="pf-c-tabs__item-text"> ${tabPanel.getAttribute("aria-label")}</span>
            </button>
        </li>`;
    }

    render(): TemplateResult {
        if (!this.tabs.size) {
            return html`<h1>${msg("no tabs defined")}</h1>`;
        }

        return html`<div class="pf-c-tabs ${this.vertical ? "pf-m-vertical pf-m-box" : ""}">
                <ul
                    class="pf-c-tabs__list"
                    role="tablist"
                    aria-orientation=${this.vertical ? "vertical" : "horizontal"}
                    aria-label=${ifPresent(this.ariaLabel)}
                >
                    ${Array.from(this.tabs, ([slotName, tabPanel]) =>
                        this.renderTab(slotName, tabPanel),
                    )}
                </ul>
            </div>
            <slot name="header"></slot>
            <slot ${ref(this.#focusTargetRef)} name=${ifPresent(this.activeTabName)}></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-tabs": Tabs;
    }
}
