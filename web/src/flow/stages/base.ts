import { AKElement } from "@goauthentik/elements/Base";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { ContextualFlowInfo, CurrentBrand, ErrorDetail } from "@goauthentik/api";

export interface SubmitOptions {
    invisible: boolean;
}

export interface StageHost {
    challenge?: unknown;
    flowSlug?: string;
    loading: boolean;
    submit(payload: unknown, options?: SubmitOptions): Promise<boolean>;

    readonly brand?: CurrentBrand;
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

// Challenge which contains flow info
export interface FlowInfoChallenge {
    flowInfo?: ContextualFlowInfo;
}

// Challenge which has a pending user
export interface PendingUserChallenge {
    pendingUser?: string;
    pendingUserAvatar?: string;
}

export class BaseStage<
    Tin extends FlowInfoChallenge & PendingUserChallenge,
    Tout,
> extends AKElement {
    host!: StageHost;

    @property({ attribute: false })
    challenge!: Tin;

    async submitForm(e: Event, defaults?: Tout): Promise<boolean> {
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

    renderUserInfo(): TemplateResult {
        if (!this.challenge.pendingUser || !this.challenge.pendingUserAvatar) {
            return html``;
        }
        return html`
            <ak-form-static
                class="pf-c-form__group"
                userAvatar="${this.challenge.pendingUserAvatar}"
                user=${this.challenge.pendingUser}
            >
                <div slot="link">
                    <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                        >${msg("Not you?")}</a
                    >
                </div>
            </ak-form-static>
            <input
                name="username"
                autocomplete="username"
                type="hidden"
                value="${this.challenge.pendingUser}"
            />
        `;
    }

    cleanup(): void {
        // Method that can be overridden by stages
        return;
    }
}
