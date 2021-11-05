import { LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import { ErrorDetail } from "@goauthentik/api";

export interface StageHost {
    challenge?: unknown;
    flowSlug: string;
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
        form.forEach((value, key) => (object[key] = value));
        this.host?.submit(object as unknown as Tout);
    }

    renderNonFieldErrors(errors: ErrorDetail[]): TemplateResult {
        if (!errors) {
            return html``;
        }
        return html`<div class="pf-c-form__alert">
            ${errors.map((err) => {
                return html`<div class="pf-c-alert pf-m-inline pf-m-danger">
                    <div class="pf-c-alert__icon">
                        <i class="fas fa-exclamation-circle"></i>
                    </div>
                    <h4 class="pf-c-alert__title">${err.string}</h4>
                </div>`;
            })}
        </div>`;
    }
}
