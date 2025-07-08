import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    AuthenticatorEmailChallenge,
    AuthenticatorEmailChallengeResponseRequest,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-email")
export class AuthenticatorEmailStage extends BaseStage<
    AuthenticatorEmailChallenge,
    AuthenticatorEmailChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return [PFBase, PFAlert, PFLogin, PFForm, PFFormControl, PFTitle, PFButton];
    }

    renderEmailInput(): TemplateResult {
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
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
                    <ak-form-element
                        label="${msg("Configure your email")}"
                        required
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.responseErrors || {}).email}
                    >
                        <input
                            type="email"
                            name="email"
                            placeholder="${msg("Please enter your email address.")}"
                            autofocus=""
                            autocomplete="email"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element>
                    ${this.renderNonFieldErrors()}
                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${msg("Continue")}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }

    renderEmailOTPInput(): TemplateResult {
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
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
                A verification token has been sent to your configured email address
                ${ifDefined(this.challenge.email)}
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
                    <ak-form-element
                        label="${msg("Code")}"
                        required
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.responseErrors || {}).code}
                    >
                        <input
                            type="text"
                            name="code"
                            inputmode="numeric"
                            pattern="[0-9]*"
                            placeholder="${msg("Please enter the code you received via email")}"
                            autofocus=""
                            autocomplete="one-time-code"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element>
                    ${this.renderNonFieldErrors()}
                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${msg("Continue")}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }

    render(): TemplateResult {
        console.debug(
            "authentik/stages/authenticator_email:",
            this.challenge ? this.challenge.emailRequired : undefined,
        );

        if (!this.challenge) {
            console.debug(
                "authentik/stages/authenticator_email: AuthenticatorEmailStage.render() called without challenge",
            );

            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
        if (this.challenge.emailRequired) {
            console.debug(
                "authentik/stages/authenticator_email: AuthenticatorEmailStage.render() called with challenge",
                this.challenge,
            );

            return this.renderEmailInput();
        }
        console.debug(
            "authentik/stages/authenticator_email: AuthenticatorEmailStage.render() called without emailRequired challenge",
            this.challenge,
        );

        return this.renderEmailOTPInput();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-email": AuthenticatorEmailStage;
    }
}
