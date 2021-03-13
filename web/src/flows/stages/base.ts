import { LitElement } from "lit-element";

export interface StageHost {
    submit<T>(formData?: T): Promise<void>;
}

export class BaseStage extends LitElement {

    host?: StageHost;

    submitForm(e: Event): void {
        e.preventDefault();
        const object: {
            [key: string]: unknown;
        } = {};
        const form = new FormData(this.shadowRoot?.querySelector("form") || undefined);
        form.forEach((value, key) => object[key] = value);
        this.host?.submit(object);
    }

}
