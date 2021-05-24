import { Challenge } from "authentik-api";
import { ChallengeResponseRequest } from "authentik-api/dist/models/ChallengeResponseRequest";
import { LitElement } from "lit-element";

export interface StageHost {
    challenge?: Challenge;
    submit(payload: ChallengeResponseRequest): Promise<void>;
}

export class BaseStage extends LitElement {

    host?: StageHost;
    challenge!: Challenge;

    submitForm(e: Event): void {
        e.preventDefault();
        const object: {
            [key: string]: unknown;
        } = {};
        const form = new FormData(this.shadowRoot?.querySelector("form") || undefined);
        form.forEach((value, key) => object[key] = value);
        this.host?.submit(object as unknown as ChallengeResponseRequest);
    }

}
