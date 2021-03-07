import { LitElement } from "lit-element";

export interface StageHost {
    submit(formData?: FormData): Promise<void>;
}

export class BaseStage extends LitElement {

    host?: StageHost;

    submitForm(e: Event): void {
        e.preventDefault();
        const form = new FormData(this.shadowRoot?.querySelector("form") || undefined);
        this.host?.submit(form);
    }

}
