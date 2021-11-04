import { LitElement, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-dropdown")
export class DropdownButton extends LitElement {
    constructor() {
        super();
        const menu = this.querySelector<HTMLElement>(".pf-c-dropdown__menu");
        this.querySelectorAll("button.pf-c-dropdown__toggle").forEach((btn) => {
            btn.addEventListener("click", () => {
                if (!menu) return;
                menu.hidden = !menu.hidden;
            });
        });
    }

    render(): TemplateResult {
        return html`<slot></slot>`;
    }
}
