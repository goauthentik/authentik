import "#elements/EmptyState";
import "#flow/components/ak-flow-card";
import "#flow/FormStatic";

import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import {
    Assertion,
    assertWebAuthnSupported,
    isWebAuthnNotAllowedError,
    transformCredentialCreateOptions,
    transformNewAssertionForServer,
} from "#common/helpers/webauthn";

import { FlowUserDetails } from "#flow/FormStatic";
import { BaseStage } from "#flow/stages/base";

import {
    AuthenticatorWebAuthnChallenge,
    AuthenticatorWebAuthnChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

export interface WebAuthnAuthenticatorRegisterChallengeResponse {
    response: Assertion;
}

@customElement("ak-stage-authenticator-webauthn")
export class WebAuthnAuthenticatorRegisterStage extends BaseStage<
    AuthenticatorWebAuthnChallenge,
    AuthenticatorWebAuthnChallengeResponseRequest
> {
    static styles: CSSResult[] = [PFLogin, PFFormControl, PFForm, PFTitle, PFButton];

    @property({ type: Boolean })
    public registerRunning = false;

    @property({ type: String, attribute: false })
    public errorMessage: string | null = null;

    protected publicKeyCredentialCreateOptions?: PublicKeyCredentialCreationOptions;

    protected async register(): Promise<unknown> {
        if (!this.challenge) {
            return;
        }

        assertWebAuthnSupported();

        if (!this.host) {
            this.logger.error("Host is not set, cannot submit registration");
            return;
        }

        // Request the authenticator(s) to create a new credential keypair.
        const credential = await navigator.credentials
            .create({
                publicKey: this.publicKeyCredentialCreateOptions,
            })
            .then((credential) => {
                if (!credential) {
                    throw new Error("Credential is empty");
                }

                return credential as PublicKeyCredential;
            })
            .catch((cause) => {
                if (isWebAuthnNotAllowedError(cause)) {
                    throw new Error(
                        msg("Registration was cancelled or timed out. Please try again."),
                        { cause },
                    );
                }

                throw new Error(
                    msg("An error occurred while creating the credential. Please try again."),
                    { cause },
                );
            });

        // we now have a new credential! We now need to encode the byte arrays
        // in the credential into strings, for posting to our server.
        const newAssertionForServer = transformNewAssertionForServer(credential);

        // post the transformed credential data to the server for validation
        // and storing the public key
        return this.host
            .submit(
                {
                    response: newAssertionForServer,
                },
                {
                    invisible: true,
                },
            )
            .catch((cause: unknown) => {
                throw new Error(msg("Server validation of credential failed"), { cause });
            });
    }

    protected tryRegister = async (): Promise<unknown> => {
        if (this.registerRunning) {
            return;
        }
        this.registerRunning = true;

        return this.register()
            .catch(async (error: unknown) => {
                const reason = msg("Failed to register. Please try again.");
                this.logger.warn("Failed to register", error);

                const parsedError = await parseAPIResponseError(error);

                this.errorMessage = pluckErrorDetail(parsedError, reason);
            })
            .finally(() => {
                this.registerRunning = false;
            });
    };

    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("challenge") && this.challenge) {
            // convert certain members of the PublicKeyCredentialCreateOptions into
            // byte arrays as expected by the spec.
            this.publicKeyCredentialCreateOptions = transformCredentialCreateOptions(
                this.challenge?.registration as PublicKeyCredentialCreationOptions,
                this.challenge?.registration.user.id,
            );
            this.tryRegister();
        }
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                ${FlowUserDetails({ challenge: this.challenge })}

                <ak-empty-state ?loading="${this.registerRunning}" icon="fa-times">
                    <span
                        >${this.registerRunning
                            ? msg("Registering...")
                            : this.errorMessage || msg("Failed to register")}
                    </span>
                </ak-empty-state>
                ${this.challenge?.responseErrors
                    ? html`<p>${this.challenge.responseErrors.response[0].string}</p>`
                    : nothing}
                <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    ${!this.registerRunning
                        ? html` <button
                              class="pf-c-button pf-m-primary pf-m-block"
                              @click=${() => {
                                  this.tryRegister();
                              }}
                              type="button"
                          >
                              ${msg("Retry registration")}
                          </button>`
                        : nothing}
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-webauthn": WebAuthnAuthenticatorRegisterStage;
    }
}
