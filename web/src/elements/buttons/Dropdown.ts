import { EVENT_REFRESH } from "#common/constants";

import { AKElement } from "#elements/Base";

import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-dropdown")
export class DropdownButton extends AKElement {
    menu: HTMLElement | null = null;

    constructor() {
        super();
        window.addEventListener(EVENT_REFRESH, this.show);
    }

    public show = (): void => {
        if (!this.menu) return;

        this.menu.hidden = true;
    };

    connectedCallback() {
        super.connectedCallback();

        const menu = this.querySelector<HTMLElement>(".pf-c-dropdown__menu");

        if (!menu) {
            console.warn("authentik/dropdown: No menu found");
        }

        this.menu = menu;

        this.querySelectorAll("button.pf-c-dropdown__toggle").forEach((btn) => {
            btn.addEventListener("click", () => {
                if (!this.menu) return;

                this.menu.hidden = !this.menu.hidden;
                btn.ariaExpanded = (!this.menu.hidden).toString();
            });
        });
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener(EVENT_REFRESH, this.show);
    }

    render(): TemplateResult {
        return html`<slot></slot>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-dropdown": DropdownButton;
    }
}
