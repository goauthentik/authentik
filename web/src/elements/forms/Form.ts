import "@polymer/paper-input/paper-input";
import "@polymer/iron-form/iron-form";
import { PaperInputElement } from "@polymer/paper-input/paper-input";
import { showMessage } from "../../elements/messages/MessageContainer";
import { customElement, html, LitElement, property, TemplateResult } from "lit-element";

export interface ErrorResponse {
    [key: string]: string[];
}

@customElement("ak-form")
export class Form extends LitElement {

    @property()
    successMessage = "";

    @property()
    send!: (data: Record<string, unknown>) => Promise<unknown>;

    submit(ev: Event): Promise<unknown> | undefined {
        ev.preventDefault();
        const ironForm = this.shadowRoot?.querySelector("iron-form");
        if (!ironForm) {
            return;
        }
        const data = ironForm.serializeForm();
        return this.send(data).then(() => {
            showMessage({
                level_tag: "success",
                message: this.successMessage
            });
        }).catch((ex: Response) => {
            if (ex.status > 399 && ex.status < 500) {
                return ex.json();
            }
            return ex;
        }).then((errorMessage?: ErrorResponse) => {
            if (!errorMessage) return;
            const elements: PaperInputElement[] = ironForm._getSubmittableElements();
            elements.forEach((element) => {
                const elementName = element.name;
                if (!elementName) return;
                if (elementName in errorMessage) {
                    element.errorMessage = errorMessage[elementName].join(", ");
                    element.invalid = true;
                }
            });
        });
    }

    render(): TemplateResult {
        return html`<iron-form
            @iron-form-presubmit=${(ev: Event) => { this.submit(ev); }}>
            <slot></slot>
        </iron-form>`;
    }

}
