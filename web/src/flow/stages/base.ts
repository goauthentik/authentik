import { pluckErrorDetail } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import { ContextualFlowInfo, CurrentBrand, ErrorDetail } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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

export interface ResponseErrorsChallenge {
    responseErrors?: {
        [key: string]: ErrorDetail[];
    };
}

export abstract class BaseStage<
    Tin extends FlowInfoChallenge & PendingUserChallenge & ResponseErrorsChallenge,
    Tout,
> extends AKElement {
    host!: StageHost;

    @property({ attribute: false })
    public challenge!: Tin;

    public submitForm = async (event?: SubmitEvent, defaults?: Tout): Promise<boolean> => {
        event?.preventDefault();

        const payload: Record<string, unknown> = defaults || {};

        const form = this.shadowRoot?.querySelector("form");

        if (form) {
            const data = new FormData(form);

            for await (const [key, value] of data.entries()) {
                if (value instanceof Blob) {
                    payload[key] = await readFileAsync(value);
                } else {
                    payload[key] = value;
                }
            }
        }

        return this.host?.submit(payload).then((successful) => {
            if (successful) {
                this.onSubmitSuccess();
            } else {
                this.onSubmitFailure();
            }

            return successful;
        });
    };

    renderNonFieldErrors() {
        const nonFieldErrors = this.challenge?.responseErrors?.non_field_errors;

        if (!nonFieldErrors) {
            return nothing;
        }

        return html`<div class="pf-c-form__alert">
            ${nonFieldErrors.map((err, idx) => {
                return html`<div
                    role="alert"
                    aria-labelledby="error-message-${idx}"
                    class="pf-c-alert pf-m-inline pf-m-danger"
                >
                    <div class="pf-c-alert__icon">
                        <i aria-hidden="true" class="fas fa-exclamation-circle"></i>
                    </div>
                    <p id="error-message-${idx}" class="pf-c-alert__title">
                        ${pluckErrorDetail(err)}
                    </p>
                </div>`;
            })}
        </div>`;
    }

    renderUserInfo() {
        if (!this.challenge.pendingUser || !this.challenge.pendingUserAvatar) {
            return nothing;
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

    onSubmitSuccess(): void {
        // Method that can be overridden by stages
        return;
    }
    onSubmitFailure(): void {
        // Method that can be overridden by stages
        return;
    }
}
