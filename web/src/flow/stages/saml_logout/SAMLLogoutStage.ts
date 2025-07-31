import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import { FlowChallengeResponseRequest, SAMLLogoutChallenge } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-saml-logout")
export class SAMLLogoutStage extends BaseStage<
    SAMLLogoutChallenge,
    FlowChallengeResponseRequest
> {
    @query("form")
    private form?: HTMLFormElement;

    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFButton,
        PFFormControl,
        PFTitle,
        css`
            .ak-hidden {
                display: none;
            }
        `,
    ];

    firstUpdated(changedProperties: PropertyValues): void {
        super.firstUpdated(changedProperties);

        // If complete, auto-submit to continue flow
        if (this.challenge.isComplete === "true") {
            const submitEvent = new Event("submit") as SubmitEvent;
            this.submitForm(submitEvent);
            return;
        }

        // If POST binding, auto-submit the form
        if (this.challenge.binding === "post" && this.form) {
            // Give a small delay to ensure DOM is ready
            setTimeout(() => {
                this.form?.submit();
            }, 100);
        }

        // If redirect binding, perform the redirect
        if (this.challenge.binding === "redirect" && this.challenge.redirectUrl) {
            setTimeout(() => {
                window.location.href = this.challenge.redirectUrl!;
            }, 100);
        }
    }

    render(): TemplateResult {
        // For complete state, just show loading (will auto-submit)
        if (this.challenge.isComplete === "true") {
            return html`<ak-flow-card .challenge=${this.challenge} loading>
                <span slot="title">${msg("Logout complete")}</span>
            </ak-flow-card>`;
        }


        // For redirect binding, just show loading and redirect
        if (this.challenge.binding === "redirect" && this.challenge.redirectUrl) {
            window.location.href = this.challenge.redirectUrl;
            return html`<ak-flow-card .challenge=${this.challenge} loading>
                <span slot="title">${msg("Redirecting to SAML provider...")}</span>
            </ak-flow-card>`;
        }

        // For POST binding, render auto-submit form
        if (this.challenge.binding === "post") {
            return html`<ak-flow-card .challenge=${this.challenge}>
                <span slot="title">${msg("SAML Single Logout")}</span>
                <form
                    class="pf-c-form"
                    action="${this.challenge.url}"
                    method="post"
                >
                    <input
                        type="hidden"
                        name="SAMLRequest"
                        value="${this.challenge.samlRequest}"
                    />
                    ${this.challenge.relayState
                        ? html`<input
                              type="hidden"
                              name="RelayState"
                              value="${this.challenge.relayState}"
                          />`
                        : html``}
                    <div class="pf-c-form__group">
                        <p>
                            ${msg(
                                `Please wait while we log you out from ${
                                    this.challenge.providerName || "SAML provider"
                                }...`,
                            )}
                        </p>
                        <noscript>
                            <p>
                                ${msg(
                                    "JavaScript is disabled. Please click the button below to continue.",
                                )}
                            </p>
                            <button type="submit" class="pf-c-button pf-m-primary">
                                ${msg("Continue")}
                            </button>
                        </noscript>
                    </div>
                </form>
            </ak-flow-card>`;
        }

        // Fallback for unknown binding
        return html`<ak-flow-card .challenge=${this.challenge} loading>
            <span slot="title">${msg("Processing logout...")}</span>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-saml-logout": SAMLLogoutStage;
    }
}
