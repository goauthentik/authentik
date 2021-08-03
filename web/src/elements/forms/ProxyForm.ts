import { customElement, html, property, TemplateResult } from "lit-element";
import { Form } from "./Form";

@customElement("ak-proxy-form")
export class ProxyForm extends Form<unknown> {
    @property()
    type!: string;

    @property({ attribute: false })
    args: Record<string, unknown> = {};

    @property({ attribute: false })
    typeMap: Record<string, string> = {};

    submit(ev: Event): Promise<unknown> | undefined {
        return (this.shadowRoot?.firstElementChild as Form<unknown>).submit(ev);
    }

    resetForm(): void {
        (this.shadowRoot?.firstElementChild as Form<unknown> | undefined)?.resetForm();
    }

    getSuccessMessage(): string {
        return (this.shadowRoot?.firstElementChild as Form<unknown>).getSuccessMessage();
    }

    async requestUpdate(name?: PropertyKey | undefined, oldValue?: unknown): Promise<unknown> {
        const result = await super.requestUpdate(name, oldValue);
        await (this.shadowRoot?.firstElementChild as Form<unknown> | undefined)?.requestUpdate();
        return result;
    }

    renderVisible(): TemplateResult {
        let elementName = this.type;
        if (this.type in this.typeMap) {
            elementName = this.typeMap[this.type];
        }
        const el = document.createElement(elementName);
        for (const k in this.args) {
            el.setAttribute(k, this.args[k] as string);
            (el as unknown as Record<string, unknown>)[k] = this.args[k];
        }
        return html`${el}`;
    }
}
