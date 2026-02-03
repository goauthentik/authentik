import { AKRefreshEvent } from "#common/events";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";

import { ConsoleLogger } from "#logger/browser";

import { customElement } from "lit/decorators.js";

@customElement("ak-dropdown")
export class DropdownButton extends AKElement {
    public static override shadowRootOptions: ShadowRootInit = {
        ...AKElement.shadowRootOptions,
        delegatesFocus: true,
    };

    protected createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    #menu: HTMLMenuElement | null = null;
    #toggleButton: HTMLButtonElement | null = null;
    #abortController: AbortController | null = null;

    protected logger = ConsoleLogger.prefix("dropdown");

    @listen(AKRefreshEvent)
    public hide = (): void => {
        if (!this.#menu || !this.#toggleButton) return;

        this.#menu.hidden = true;
        this.#toggleButton.ariaExpanded = "false";
    };

    public toggleMenu = (event: MouseEvent): void => {
        if (!this.#menu) return;

        const button = event.currentTarget as HTMLButtonElement;

        this.#menu.hidden = !this.#menu.hidden;
        button.ariaExpanded = this.#menu.hidden.toString();

        event.stopPropagation();
    };

    @listen("click", {
        passive: true,
    })
    protected clickHandler = (event: Event): void => {
        if (!this.#menu) return;

        if (this.#menu.hidden) {
            return;
        }

        if (event.defaultPrevented) {
            return;
        }

        const target = event.target as HTMLElement;
        if (this.#menu.contains(target)) {
            return;
        }
        const toggle = this.querySelector<HTMLElement>("button.pf-c-dropdown__toggle");
        if (toggle && toggle.contains(target)) {
            return;
        }

        this.hide();
    };

    public override connectedCallback() {
        super.connectedCallback();

        this.#abortController = new AbortController();

        this.#menu = this.querySelector<HTMLMenuElement>("menu.pf-c-dropdown__menu");

        if (!this.#menu) {
            this.logger.warn("No menu found");
            return;
        }

        this.#toggleButton = this.querySelector<HTMLButtonElement>("button.pf-c-dropdown__toggle");

        if (!this.#toggleButton) {
            this.logger.warn("No toggle button found");
            return;
        }

        this.#menu.hidden = true;
        this.#toggleButton.ariaExpanded = "false";

        this.#toggleButton.addEventListener("click", this.toggleMenu, {
            capture: true,
            signal: this.#abortController.signal,
        });

        // TODO: Enable this after native <dialog> modals are used.
        // If enabled now, this would close the modal since it's technically within the dropdown.
        // const menuItemButtons = this.querySelectorAll<HTMLElement>(".pf-c-dropdown__menu-item");

        // for (const menuItemButton of menuItemButtons) {
        //     menuItemButton.addEventListener("click", this.hide, {
        //         capture: true,
        //         signal: this.#abortController.signal,
        //     });
        // }
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#abortController?.abort();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-dropdown": DropdownButton;
    }
}
