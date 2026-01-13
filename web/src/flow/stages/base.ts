import { pluckErrorDetail } from "#common/errors/network";

import { AKElement } from "#elements/Base";
import { intersectionObserver } from "#elements/decorators/intersection-observer";
import { WithLocale } from "#elements/mixins/locale";
import { FocusTarget } from "#elements/utils/focus";

import { FlowUserDetails } from "#flow/FormStatic";

import { ConsoleLogger } from "#logger/browser";

import { ContextualFlowInfo, CurrentBrand, ErrorDetail } from "@goauthentik/api";

import { html, LitElement, nothing, PropertyValues } from "lit";
import { property } from "lit/decorators.js";

export interface SubmitOptions {
    invisible: boolean;
}

export interface StageHost {
    challenge?: unknown;
    flowSlug?: string;
    loading: boolean;
    reset?: () => void;
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
> extends WithLocale(AKElement) {
    static shadowRootOptions: ShadowRootInit = {
        ...LitElement.shadowRootOptions,
        delegatesFocus: true,
    };

    protected logger = ConsoleLogger.prefix(`flow:${this.tagName.toLowerCase()}`);

    // TODO: Should have a property but this needs some refactoring first.
    // @property({ attribute: false })
    public host!: StageHost;

    @property({ attribute: false })
    public challenge!: Tin;

    @intersectionObserver()
    public visible = false;

    protected autofocusTarget = new FocusTarget();
    focus = this.autofocusTarget.focus;

    #visibilityListener = () => {
        if (document.visibilityState !== "visible") return;
        if (!this.visible) return;

        if (!this.autofocusTarget.target) return;

        this.autofocusTarget.focus();
    };

    public override connectedCallback(): void {
        super.connectedCallback();

        this.addEventListener("focus", this.autofocusTarget.toEventListener());

        document.addEventListener("visibilitychange", this.#visibilityListener);
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();

        this.removeEventListener("focus", this.autofocusTarget.toEventListener());

        document.removeEventListener("visibilitychange", this.#visibilityListener);
    }

    public updated(changed: PropertyValues<this>): void {
        super.updated(changed);

        // We're especially mindful of how often this runs to avoid
        // unnecessary focus and in-fighting between the user's chosen focus target.
        if (
            changed.has("visible") &&
            changed.get("visible") !== this.visible &&
            this.visible &&
            this.autofocusTarget.target
        ) {
            this.autofocusTarget.focus();
        }
    }

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

        return this.host?.submit(payload).then(async (successful) => {
            if (successful) {
                await this.onSubmitSuccess?.(payload);
            } else {
                await this.onSubmitFailure?.(payload);
            }

            return successful;
        });
    };

    protected renderNonFieldErrors() {
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

    protected renderUserInfo() {
        if (!this.challenge.pendingUser || !this.challenge.pendingUserAvatar) {
            return nothing;
        }
        return html`
            ${FlowUserDetails({ challenge: this.challenge })}
            <input
                name="username"
                autocomplete="username"
                type="hidden"
                value="${this.challenge.pendingUser}"
            />
        `;
    }

    /**
     * Callback method for successful form submission.
     *
     * @abstract
     */
    protected onSubmitSuccess?(payload: Record<string, unknown>): void | Promise<void>;

    /**
     * Callback method for failed form submission.
     *
     * @abstract
     */
    protected onSubmitFailure?(payload: Record<string, unknown>): void | Promise<void>;
}
