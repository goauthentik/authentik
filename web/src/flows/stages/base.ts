import { LitElement, property } from "lit-element";

export interface StageHost {
    challenge?: unknown;
    submit(payload: unknown): Promise<void>;
}

export class BaseStage<Tin, Tout> extends LitElement {

    host!: StageHost;

    @property({ attribute: false })
    challenge!: Tin;

    submitForm(e: Event): void {
        e.preventDefault();
        const object: {
            [key: string]: unknown;
        } = {};
        const form = new FormData(this.shadowRoot?.querySelector("form") || undefined);
        form.forEach((value, key) => object[key] = value);
        this.host?.submit(object as unknown as Tout);
    }

}
