import {
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "@goauthentik/common/helpers/webauthn";
import { AuthenticatorValidateStage } from "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest,
    DeviceChallenge,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-validate-webauthn")
export class AuthenticatorValidateStageWebAuthn extends BaseStage<
    AuthenticatorValidationChallenge,
    AuthenticatorValidationChallengeResponseRequest
> {
    @property({ attribute: false })
    deviceChallenge?: DeviceChallenge;

    @property()
    authenticateMessage?: string;

    @property({ type: Boolean })
    showBackButton = false;

    transformedCredentialRequestOptions?: PublicKeyCredentialRequestOptions;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFEmptyState,
            PFBullseye,
            PFForm,
            PFFormControl,
            PFTitle,
            PFButton,
        ];
    }

    async authenticate(): Promise<void> {
        // request the authenticator to create an assertion signature using the
        // credential private key
        let assertion;
        try {
            assertion = await navigator.credentials.get({
                publicKey: this.transformedCredentialRequestOptions,
            });
            if (!assertion) {
                throw new Error(msg("Assertions is empty"));
            }
        } catch (err) {
            throw new Error(msg(str`Error when creating credential: ${err}`));
        }

        // we now have an authentication assertion! encode the byte arrays contained
        // in the assertion data as strings for posting to the server
        const transformedAssertionForServer = transformAssertionForServer(
            assertion as PublicKeyCredential,
        );

        // post the assertion to the server for verification.
        try {
            await this.host?.submit({
                webauthn: transformedAssertionForServer,
            });
        } catch (err) {
            throw new Error(msg(str`Error when validating assertion on server: ${err}`));
        }
    }

    firstUpdated(): void {
        // convert certain members of the PublicKeyCredentialRequestOptions into
        // byte arrays as expected by the spec.
        const credentialRequestOptions = this.deviceChallenge
            ?.challenge as PublicKeyCredentialRequestOptions;
        this.transformedCredentialRequestOptions =
            transformCredentialRequestOptions(credentialRequestOptions);
        this.authenticateWrapper();
    }

    async authenticateWrapper(): Promise<void> {
        if (this.host.loading) {
            return;
        }
        this.host.loading = true;
        this.authenticate()
            .catch((e) => {
                console.error(e);
                this.authenticateMessage = e.toString();
            })
            .finally(() => {
                this.host.loading = false;
            });
    }

    render(): TemplateResult {
        return html`<div class="pf-c-login__main-body">
                ${this.authenticateMessage
                    ? html`<div class="pf-c-form__group pf-m-action">
                          <p class="pf-m-block">${this.authenticateMessage}</p>
                          <button
                              class="pf-c-button pf-m-primary pf-m-block"
                              @click=${() => {
                                  this.authenticateWrapper();
                              }}
                          >
                              ${msg("Retry authentication")}
                          </button>
                      </div>`
                    : html`<div class="pf-c-form__group pf-m-action">
                          <p class="pf-m-block">&nbsp;</p>
                          <p class="pf-m-block">&nbsp;</p>
                          <p class="pf-m-block">&nbsp;</p>
                      </div> `}
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                    ${this.showBackButton
                        ? html`<li class="pf-c-login__main-footer-links-item">
                              <button
                                  class="pf-c-button pf-m-secondary pf-m-block"
                                  @click=${() => {
                                      if (!this.host) return;
                                      (
                                          this.host as AuthenticatorValidateStage
                                      ).selectedDeviceChallenge = undefined;
                                  }}
                              >
                                  ${msg("Return to device picker")}
                              </button>
                          </li>`
                        : html``}
                </ul>
            </footer>`;
    }
}
