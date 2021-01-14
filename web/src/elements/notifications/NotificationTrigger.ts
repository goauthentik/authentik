import { customElement, html, LitElement, TemplateResult } from "lit-element";

@customElement("ak-notification-trigger")
export class NotificationTrigger extends LitElement {

    constructor() {
        super();
        this.addEventListener("click", () => {
            this.dispatchEvent(
                new CustomEvent("ak-notification-toggle", {
                    bubbles: true,
                    composed: true,
                })
            );
        });
    }

    render(): TemplateResult {
        return html`<slot></slot>`;
    }

}
