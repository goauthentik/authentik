import "#elements/EmptyState";

import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import {
    assertWebAuthnSupported,
    ensurePublicKeyCredential,
    isWebAuthnNotAllowedError,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "#common/helpers/webauthn";

import { SlottedTemplateResult } from "#elements/types";

import { ErrorProp } from "#components/ak-field-errors";

import { BaseDeviceStage } from "#flow/stages/authenticator_validate/base";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { map } from "lit/directives/map.js";

@customElement("ak-stage-authenticator-validate-webauthn")
export class AuthenticatorValidateStageWebAuthn extends BaseDeviceStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    @property({ attribute: false })
    public errorMessages: readonly ErrorProp[] | null = null;

    @state()
    protected authenticating = true;

    protected transformedCredentialRequestOptions: PublicKeyCredentialRequestOptions | null = null;

    /**
     * Whether a {@linkcode https://developer.mozilla.org/en-US/docs/Web/API/PublicKeyCredential | PublicKeyCredential} ceremony should start once the pending render has committed.
     *
     * Reactive state is derived in {@linkcode willUpdate} so it lands in the same render, but the
     * ceremony itself is a side effect and belongs after the DOM has been written.
     */
    protected ceremonyPending = false;

    #authenticate = async (): Promise<unknown> => {
        return this.authenticate().catch(async (error: unknown) => {
            const reason = msg("Failed to authenticate");
            this.logger.warn(reason, error);

            const parsedError = await parseAPIResponseError(error);

            this.errorMessages = [parsedError];
            this.authenticating = false;

            return false;
        });
    };

    protected async authenticate(): Promise<boolean> {
        assertWebAuthnSupported();

        // Request the authenticator to create an assertion signature using the
        // credential private key.

        const assertion = await navigator.credentials
            .get({ publicKey: this.transformedCredentialRequestOptions || undefined })
            .then(ensurePublicKeyCredential)
            .catch((cause: unknown) => {
                if (isWebAuthnNotAllowedError(cause)) {
                    throw new Error(msg("Authentication was cancelled or timed out"), { cause });
                }

                throw new Error("Error creating credential", { cause });
            });

        // We now have an authentication assertion! encode the byte arrays contained
        // in the assertion data as strings for posting to the server

        // Post the assertion to the server for verification.
        return this.host
            ?.submit({ webauthn: transformAssertionForServer(assertion) }, { invisible: true })
            .catch((cause: unknown) => {
                throw new Error(`Error when validating assertion on server`, { cause });
            });
    }

    protected tryAuthenticating = async (): Promise<unknown> => {
        if (this.authenticating) {
            return;
        }

        this.errorMessages = null;
        this.authenticating = true;

        return this.#authenticate();
    };

    // #region Lifecycle

    protected override willUpdate(changedProperties: PropertyValues<this>): void {
        super.willUpdate(changedProperties);

        if (!changedProperties.has("challenge") || !this.challenge) return;

        this.errorMessages = null;

        // convert certain members of the PublicKeyCredentialRequestOptions into
        // byte arrays as expected by the spec.
        const credentialRequestOptions = this.deviceChallenge
            ?.challenge as PublicKeyCredentialRequestOptions;
        this.transformedCredentialRequestOptions =
            transformCredentialRequestOptions(credentialRequestOptions);

        const responseErrors = Object.values(this.challenge.responseErrors ?? {}).flat();

        if (responseErrors.length) {
            this.errorMessages = responseErrors.some((error) => error.string)
                ? responseErrors
                : [msg("Failed to authenticate")];

            this.authenticating = false;

            return;
        }

        this.ceremonyPending = true;
        this.authenticating = true;
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (!this.ceremonyPending) return;

        this.ceremonyPending = false;

        this.#authenticate();
    }

    // #endregion

    // #region Rendering

    protected renderAuthenticationActions(): SlottedTemplateResult {
        const errorMessages = this.errorMessages ?? [];

        if (!errorMessages.length && !this.showBackButton) {
            return null;
        }

        return html`<fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
            <legend class="sr-only">${msg("Form actions")}</legend>
            ${errorMessages.length
                ? html`<button
                      class="pf-c-button pf-m-primary pf-m-block"
                      @click=${this.tryAuthenticating}
                      type="button"
                  >
                      ${msg("Retry authentication")}
                  </button>`
                : null}
            ${this.renderReturnToDevicePicker()}
        </fieldset>`;
    }

    protected renderAuthenticationStatus(): SlottedTemplateResult {
        const { errorMessages } = this;

        if (!errorMessages?.length) {
            return html`<div>${msg("Authenticating...")}</div>`;
        }

        return map(errorMessages, (error) => {
            const detail = pluckErrorDetail(error);

            return html`<p role="alert">${detail}</p>`;
        });
    }

    protected override render(): SlottedTemplateResult {
        const hasError = !!this.errorMessages?.length;
        const loading = this.authenticating || !hasError;

        return html`<form class="pf-c-form">
            ${this.renderUserInfo()}
            <ak-empty-state ?loading=${loading} icon="fa-times">
                ${this.renderAuthenticationStatus()}
            </ak-empty-state>
            ${this.renderAuthenticationActions()}
        </form>`;
    }

    // #endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate-webauthn": AuthenticatorValidateStageWebAuthn;
    }
}
