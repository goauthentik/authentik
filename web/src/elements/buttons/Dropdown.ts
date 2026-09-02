import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKRefreshEvent } from "#common/events";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";

import { ConsoleLogger } from "#logger/browser";

import type { PfTooltip } from "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { customElement } from "lit/decorators.js";

/**
 * Enter events sourced from pf-tooltip.
 */
const EnterEvents = ["focusin", "tap", "mouseenter"];

@customElement("ak-dropdown")
export class DropdownButton extends AKElement {
    public static SplitButtonSelector = `.pf-c-dropdown__toggle.pf-m-split-button .pf-c-dropdown__toggle-button:last-child`;
    public static ToggleButtonSelector = `.pf-c-dropdown__toggle:not(.pf-m-split-button)`;

    public static override shadowRootOptions: ShadowRootInit = {
        ...AKElement.shadowRootOptions,
        delegatesFocus: true,
    };

    protected createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    protected menu: HTMLMenuElement | null = null;
    protected toggleButton: HTMLButtonElement | null = null;
    protected tooltip: PfTooltip | null = null;
    protected abortController: AbortController | null = null;

    protected logger = ConsoleLogger.prefix("dropdown");

    @listen(AKRefreshEvent, { target: window })
    public hide = (): void => {
        if (!this.menu || !this.toggleButton) return;

        this.menu.hidden = true;
        this.toggleButton.ariaExpanded = "false";
    };

    public toggleMenu = (event: MouseEvent): void => {
        if (!this.menu) return;

        const button = event.currentTarget as HTMLButtonElement;

        this.menu.hidden = !this.menu.hidden;
        button.ariaExpanded = (!this.menu.hidden).toString();

        event.stopPropagation();
        this.tooltip?.hide();
    };

    @listen("click", { target: window })
    protected clickHandler = (event: Event): void => {
        if (!this.menu) return;

        if (this.menu.hidden) {
            return;
        }

        if (event.defaultPrevented) {
            return;
        }

        const target = event.target as HTMLElement;

        if (this.menu.contains(target)) {
            return;
        }

        this.hide();
    };

    public override connectedCallback() {
        super.connectedCallback();

        this.abortController = new AbortController();

        this.menu = this.querySelector<HTMLMenuElement>("menu.pf-c-dropdown__menu");

        if (!this.menu) {
            this.logger.warn("No menu found");
            return;
        }

        this.toggleButton =
            this.querySelector(DropdownButton.SplitButtonSelector) ||
            this.querySelector(DropdownButton.ToggleButtonSelector);

        if (!this.toggleButton) {
            this.logger.warn("No toggle button found");
            return;
        }

        this.menu.hidden = true;
        this.toggleButton.ariaExpanded = "false";

        this.toggleButton.addEventListener("click", this.toggleMenu, {
            capture: true,
            signal: this.abortController.signal,
        });

        const menuItemButtons = this.querySelectorAll<HTMLElement>(".pf-c-dropdown__menu-item");

        for (const menuItemButton of menuItemButtons) {
            menuItemButton.addEventListener("click", this.hide, {
                capture: true,
                signal: this.abortController.signal,
            });
        }

        this.tooltip = this.querySelector("pf-tooltip");

        if (this.tooltip && !this.tooltip.hasAttribute("trigger")) {
            const trigger = this.querySelector("[data-tooltip-target]") || this;
            console.debug("Setting tooltip trigger to", trigger);

            this.tooltip.trigger = trigger;

            for (const eventName of EnterEvents) {
                this.addEventListener(eventName, this.interceptTooltipEvent, { capture: true });
            }
        }
    }

    /**
     * Intercepts tooltip events and prevents them from propagating when the menu is open.
     * This ensures that the tooltip does not interfere with the dropdown menu's behavior.
     */
    protected interceptTooltipEvent = (event: Event): void => {
        if (!this.tooltip) return;

        const menuHidden = this.menu && this.menu.hidden;

        if (event.type === "click" && !menuHidden) {
            this.hide();
        }

        if (!menuHidden) {
            event.stopPropagation();
        }
    };

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.abortController?.abort();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-dropdown": DropdownButton;
    }
}
