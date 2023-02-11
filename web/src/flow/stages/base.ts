import { AKElement } from "@goauthentik/elements/Base";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";

import { TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import { CurrentTenant, ErrorDetail } from "@goauthentik/api";

export interface StageHost {
    challenge?: unknown;
    flowSlug?: string;
    loading: boolean;
    submit(payload: unknown): Promise<boolean>;

    readonly tenant: CurrentTenant;
}

export function readFileAsync(file: Blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            resolve(reader.result);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

export class BaseStage<Tin, Tout> extends AKElement {
    host!: StageHost;

    @property({ attribute: false })
    challenge!: Tin;

    async submitForm(e: Event, defaults?: KeyUnknown): Promise<boolean> {
        e.preventDefault();
        const object: KeyUnknown = defaults || {};
        const form = new FormData(this.shadowRoot?.querySelector("form") || undefined);

        for await (const [key, value] of form.entries()) {
            if (value instanceof Blob) {
                object[key] = await readFileAsync(value);
            } else {
                object[key] = value;
            }
        }
        return this.host?.submit(object as unknown as Tout).then((successful) => {
            if (successful) {
                this.cleanup();
            }
            return successful;
        });
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

    cleanup(): void {
        // Method that can be overridden by stages
        return;
    }
}
