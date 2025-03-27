import { Form } from "@goauthentik/elements/forms/Form";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-proxy-form")
export abstract class ProxyForm extends Form<unknown> {
    @property()
    type!: string;

    // TODO: Is this used anywhere?
    @property({ attribute: false })
    args: Record<string, unknown> = {};

    @property({ attribute: false })
    typeMap: Record<string, string> = {};

    innerElement?: Form<unknown>;

    async submit(ev: Event): Promise<unknown | undefined> {
        return this.innerElement?.submit(ev);
    }

    resetForm(): void {
        this.innerElement?.resetForm();
    }

    getSuccessMessage(): string {
        return this.innerElement?.getSuccessMessage() || "";
    }

    requestUpdate(name?: PropertyKey | undefined, oldValue?: unknown): void {
        const result = super.requestUpdate(name, oldValue);
        this.innerElement?.requestUpdate();
        return result;
    }

    renderVisible(): TemplateResult {
        let elementName = this.type;

        if (this.type in this.typeMap) {
            elementName = this.typeMap[this.type];
        }

        if (!this.innerElement) {
            this.innerElement = document.createElement(elementName) as Form<unknown>;
        }

        this.innerElement.viewportCheck = this.viewportCheck;

        for (const [key, value] of Object.entries(this.args)) {
            this.innerElement.setAttribute(key, value as string);

            (this.innerElement as unknown as Record<string, string>)[key] = value as string;
        }
        return html`${this.innerElement}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-proxy-form": ProxyForm;
    }
}
