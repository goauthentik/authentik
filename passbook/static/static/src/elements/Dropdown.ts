import { customElement, html, LitElement } from "lit-element";

@customElement("pb-dropdown")
export class DropdownButton extends LitElement {
    constructor() {
        super();
        const menu = <HTMLElement>this.querySelector(".pf-c-dropdown__menu")!;
        this.querySelectorAll("button").forEach((btn) => {
            btn.addEventListener("click", (e) => {
                menu.hidden = !menu.hidden;
            });
        });
    }

    render() {
        return html`<slot></slot>`;
    }
}
