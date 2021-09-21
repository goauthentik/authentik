import { html, LitElement, TemplateResult } from "lit";
import { customElement } from "lit/decorators";

@customElement("ak-dropdown")
export class DropdownButton extends LitElement {
    constructor() {
        super();
        const menu = <HTMLElement>this.querySelector(".pf-c-dropdown__menu");
        this.querySelectorAll("button.pf-c-dropdown__toggle").forEach((btn) => {
            btn.addEventListener("click", () => {
                menu.hidden = !menu.hidden;
            });
        });
    }

    render(): TemplateResult {
        return html`<slot></slot>`;
    }
}
