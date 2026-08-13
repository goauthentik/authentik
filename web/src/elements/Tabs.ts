import { CURRENT_CLASS, EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";
import {
    CommandPaletteState,
    PaletteCommandAction,
    PaletteCommandDefinitionInit,
} from "#elements/commands/shared";
import { intersectionObserver } from "#elements/decorators/intersection-observer";
import { navigate, RouterNavigateEvent } from "#elements/router/core/navigation";
import { getSearchParams, updateSearchParams } from "#elements/router/core/search-params";
import Styles from "#elements/Tabs.css" with { type: "bundled-text" };
import { routedTabBaseContext } from "#elements/tabs/tab-context";
import { activeSlotForPath, tabHref } from "#elements/tabs/tab-path";
import { ifPresent } from "#elements/utils/attributes";
import { isFocusable } from "#elements/utils/focus";

import { capitalCase } from "change-case";

import { ContextConsumer, ContextProvider } from "@lit/context";
import { msg, str } from "@lit/localize";
import { CSSResult, html, LitElement, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

@customElement("ak-tabs")
export class Tabs extends AKElement {
    static shadowRootOptions = {
        ...LitElement.shadowRootOptions,
        delegatesFocus: true,
    };
    static styles: CSSResult[] = [Styles];

    /**
     * Opt into path routing: the active tab becomes a path segment
     * (`/if/user/settings/sessions`) and switching tabs navigates the router.
     * The base comes from {@linkcode routedTabBaseContext} — provided by the
     * router outlet for the page, then refined by each nested group — so no
     * page wiring is needed. Without this (and without {@linkcode base}), the
     * group falls back to the legacy `?page=` search parameter.
     */
    @property({ type: Boolean })
    public routed = false;

    /**
     * An explicit mount path override, e.g. `/if/user/settings`. Rarely needed:
     * prefer {@linkcode routed} and let the context supply the base. Setting it
     * implies {@linkcode routed}.
     */
    @property({ type: String })
    public base = "";

    /**
     * The search parameter used to persist the active tab in the legacy
     * (non-{@linkcode base}) mode.
     */
    @property({ type: String })
    public pageIdentifier = "page";

    @property({ type: Boolean, useDefault: true })
    public vertical = false;

    @state()
    protected activeTabName: string | null = null;

    @state()
    protected tabs: ReadonlyMap<string, Element> = new Map();
    /**
     * Whether the tab is visible in the viewport.
     */
    @intersectionObserver()
    public visible = false;

    #focusTargetRef = createRef<HTMLSlotElement>();
    #observer: MutationObserver | null = null;

    #commands = new CommandPaletteState<string>();

    //#region Routed base

    /**
     * The base supplied by the nearest routed ancestor (the outlet, or a parent
     * tab group), consumed reactively.
     */
    #baseConsumer = new ContextConsumer(this, {
        context: routedTabBaseContext,
        subscribe: true,
        callback: () => {
            if (!this.#pathMode) return;

            this.activeTabName = this.#slotFromLocation();
            this.#publishChildBase();
        },
    });

    /**
     * Provides this group's active-panel path to its subtree, so a nested
     * `<ak-tabs routed>` derives its base with no wiring.
     */
    #childBaseProvider = new ContextProvider(this, {
        context: routedTabBaseContext,
        initialValue: "",
    });

    #publishChildBase(): void {
        this.#childBaseProvider.setValue(
            this.activeTabName ? this.#hrefForSlot(this.activeTabName) : this.#effectiveBase,
        );
    }

    /**
     * The mount path this group tracks against: an explicit {@linkcode base}
     * wins, else the context value from the nearest routed ancestor.
     */
    get #effectiveBase(): string {
        return this.base || this.#baseConsumer.value || "";
    }

    /**
     * Whether the active tab is tracked as a path segment rather than a search
     * parameter.
     */
    get #pathMode(): boolean {
        return this.routed || Boolean(this.base);
    }

    //#endregion

    #updateTabs = (): void => {
        this.tabs = new Map(
            Array.from(this.querySelectorAll(":scope > [slot^='page-']"), (element) => {
                return [element.getAttribute("slot") || "", element];
            }),
        );

        requestAnimationFrame(this.#updateCommands);
    };

    #updateCommands = (): void => {
        const commands: PaletteCommandDefinitionInit<string>[] = [];

        if (!this.visible) {
            this.#commands.clear();
            return;
        }

        const group = msg(str`Landmark: ${capitalCase(this.pageIdentifier)}`);
        const prefix = msg("Switch to tab", { id: "command-palette.switch-to-tab" });

        const action: PaletteCommandAction<string> = (slotName) => {
            this.activateTab(slotName);
        };

        for (const [slotName, tabPanel] of this.tabs) {
            if (this.activeTabName === slotName) {
                continue;
            }

            const label = tabPanel.getAttribute("aria-label") || slotName;

            commands.push({
                label,
                action,
                group,
                prefix,
                details: slotName,
            });
        }

        this.#commands.set(commands);
    };

    //#region Navigation

    /**
     * The active slot for the current location, or `null` when the tabs are not
     * yet known. Falls back to the first tab when the path names no known tab.
     */
    #slotFromLocation(): string | null {
        return activeSlotForPath(this.#effectiveBase, window.location.pathname, [
            ...this.tabs.keys(),
        ]);
    }

    #hrefForSlot(slotName: string): string {
        return tabHref(this.#effectiveBase, slotName, this.tabs.keys().next().value ?? null);
    }

    #onNavigate = (): void => {
        if (!this.#pathMode) return;

        const nextSlot = this.#slotFromLocation();

        if (!nextSlot || nextSlot === this.activeTabName) return;

        this.activeTabName = nextSlot;
        this.#publishChildBase();
        this.dispatchActivateEvent();
    };

    //#endregion

    public override connectedCallback(): void {
        super.connectedCallback();

        this.#observer = new MutationObserver(this.#updateTabs);

        this.addEventListener("focus", this.#delegateFocusListener);

        window.addEventListener("popstate", this.#onNavigate);
        window.addEventListener(RouterNavigateEvent.eventName, this.#onNavigate);

        if (this.activeTabName) return;

        this.#updateTabs();

        if (this.#pathMode) {
            this.activeTabName = this.#slotFromLocation();
            this.#publishChildBase();
            return;
        }

        const params = getSearchParams();
        const tabParam = params[this.pageIdentifier];

        if (
            tabParam &&
            typeof tabParam === "string" &&
            this.querySelector(`[slot='${tabParam}']`)
        ) {
            this.activeTabName = tabParam;
        } else {
            this.activeTabName = this.tabs.keys().next().value || null;
        }
    }

    public override firstUpdated(): void {
        this.#observer?.observe(this, {
            attributes: true,
            childList: true,
            subtree: true,
        });

        this.dispatchActivateEvent();
    }

    public override disconnectedCallback(): void {
        this.#observer?.disconnect();
        this.#commands.clear();

        window.removeEventListener("popstate", this.#onNavigate);
        window.removeEventListener(RouterNavigateEvent.eventName, this.#onNavigate);

        super.disconnectedCallback();
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("visible")) {
            this.#updateCommands();
        }
    }

    public findActiveTabPanel(): Element | null {
        return this.querySelector(`[slot='${this.activeTabName}']`);
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

        if (this.#pathMode) {
            navigate(this.#hrefForSlot(nextTabName));
        } else {
            const firstTab = this.tabs.keys().next().value || null;

            // We avoid adding the tab parameter to the URL if it's the first tab
            // to both reduce URL length and ensure that tests do not have to deal with
            // unnecessary URL parameters.

            updateSearchParams({
                [this.pageIdentifier]: nextTabName === firstTab ? null : nextTabName,
            });
        }

        this.activeTabName = nextTabName;

        if (this.#pathMode) {
            this.#publishChildBase();
        }

        this.dispatchActivateEvent();
    }

    public dispatchActivateEvent(tabPanel = this.findActiveTabPanel()): void {
        if (!tabPanel) {
            console.warn("Cannot dispatch activate event, no tab panel found");
            return;
        }

        tabPanel.dispatchEvent(new CustomEvent(EVENT_REFRESH));
        tabPanel.dispatchEvent(new CustomEvent("activate"));
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

    #onTabClick(event: MouseEvent, slotName: string): void {
        // A modified click (new tab, download) or a non-primary button is left
        // to the browser so real links keep working; the top outlet's anchor
        // interceptor claims the rest, but activate directly as a fallback.
        if (event.button !== 0) return;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

        event.preventDefault();
        this.activateTab(slotName);
    }

    renderTab(slotName: string, tabPanel: Element): TemplateResult {
        const current = slotName === this.activeTabName;
        const label = tabPanel.getAttribute("aria-label");

        // Path mode renders a real in-interface link (accessible, middle-click
        // opens the tab's URL); legacy mode keeps the button-driven behavior.
        const control = this.#pathMode
            ? html`<a
                  href=${this.#hrefForSlot(slotName)}
                  role="tab"
                  part="tab-button"
                  id=${`${slotName}-tab`}
                  aria-selected=${current ? "true" : "false"}
                  aria-controls=${ifPresent(slotName)}
                  class="pf-c-tabs__link"
                  @click=${(event: MouseEvent) => this.#onTabClick(event, slotName)}
              >
                  <span class="pf-c-tabs__item-text">${label}</span>
              </a>`
            : html`<button
                  type="button"
                  role="tab"
                  part="tab-button"
                  id=${`${slotName}-tab`}
                  name=${slotName}
                  aria-selected=${current ? "true" : "false"}
                  aria-controls=${ifPresent(slotName)}
                  class="pf-c-tabs__link"
                  @click=${() => this.activateTab(slotName)}
              >
                  <span class="pf-c-tabs__item-text">${label}</span>
              </button>`;

        return html` <li part="tab-item" class="pf-c-tabs__item ${current ? CURRENT_CLASS : ""}">
            ${control}
        </li>`;
    }

    render(): TemplateResult {
        if (!this.tabs.size) {
            return html`<h1>${msg("no tabs defined")}</h1>`;
        }

        return html`<div
                class="pf-c-tabs ${this.vertical ? "pf-m-vertical pf-m-box" : ""}"
                part="container ${this.vertical ? "column" : "row"}"
            >
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
