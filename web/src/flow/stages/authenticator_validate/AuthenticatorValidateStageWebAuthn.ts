import "#elements/EmptyState";

import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import {
    assertWebAuthnSupported,
    isWebAuthnNotAllowedError,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "#common/helpers/webauthn";

import { SlottedTemplateResult } from "#elements/types";

import { BaseDeviceStage } from "#flow/stages/authenticator_validate/base";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceChallenge,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-stage-authenticator-validate-webauthn")
export class AuthenticatorValidateStageWebAuthn extends BaseDeviceStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    @property({ attribute: false })
    public deviceChallenge?: DeviceChallenge;

    @property({ attribute: false })
    public errorMessage?: string;

    @property({ type: Boolean })
    public showBackButton = false;

    @state()
    protected authenticating = false;

    transformedCredentialRequestOptions?: PublicKeyCredentialRequestOptions;

    protected async authenticate(): Promise<boolean> {
        assertWebAuthnSupported();

        // request the authenticator to create an assertion signature using the
        // credential private key

        const assertion = await navigator.credentials
            .get({
                publicKey: this.transformedCredentialRequestOptions,
            })
            .then((assertion) => {
                if (!assertion) {
                    throw new Error(msg("No assertion was returned by the authenticator"));
                }

                return assertion as PublicKeyCredential;
            })
            .catch((cause) => {
                if (isWebAuthnNotAllowedError(cause)) {
                    throw new Error(msg("Authentication was cancelled or timed out"), { cause });
                }

                throw new Error("Error creating credential", { cause });
            });

        // We now have an authentication assertion! encode the byte arrays contained
        // in the assertion data as strings for posting to the server

        const transformedAssertionForServer = transformAssertionForServer(assertion);

        // Post the assertion to the server for verification.
        return this.host
            ?.submit(
                {
                    webauthn: transformedAssertionForServer,
                },
                {
                    invisible: true,
                },
            )
            .catch((cause) => {
                throw new Error(`Error when validating assertion on server`, { cause });
            });
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("challenge") && this.challenge) {
            // convert certain members of the PublicKeyCredentialRequestOptions into
            // byte arrays as expected by the spec.
            const credentialRequestOptions = this.deviceChallenge
                ?.challenge as PublicKeyCredentialRequestOptions;
            this.transformedCredentialRequestOptions =
                transformCredentialRequestOptions(credentialRequestOptions);

            this.tryAuthenticating();
        }
    }

    protected tryAuthenticating = async (): Promise<unknown> => {
        if (this.authenticating) {
            return;
        }

        this.authenticating = true;

        return this.authenticate()
            .catch(async (error: unknown) => {
                const reason = msg("Failed to authenticate");
                this.logger.warn(reason, error);

                const parsedError = await parseAPIResponseError(error);

                this.errorMessage = pluckErrorDetail(parsedError, reason);
            })
            .finally(() => {
                this.authenticating = false;
            });
    };

    protected override render(): SlottedTemplateResult {
        return html`<form class="pf-c-form">
            ${this.renderUserInfo()}
            <ak-empty-state ?loading="${this.authenticating}" icon="fa-times">
                <span
                    >${this.authenticating
                        ? msg("Authenticating...")
                        : this.errorMessage || msg("Loading")}</span
                >
            </ak-empty-state>
            ${!this.authenticating || this.showBackButton
                ? html`<fieldset class="pf-c-form__group pf-m-action">
                      <legend class="sr-only">${msg("Form actions")}</legend>
                      ${!this.authenticating
                          ? html`<button
                                class="pf-c-button pf-m-primary pf-m-block"
                                @click=${this.tryAuthenticating}
                                type="button"
                            >
                                ${msg("Retry authentication")}
                            </button>`
                          : nothing}
                      ${this.renderReturnToDevicePicker()}
                  </fieldset>`
                : nothing}
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-validate-webauthn": AuthenticatorValidateStageWebAuthn;
    }
}
