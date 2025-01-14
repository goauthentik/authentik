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
    AuthenticatorSMSChallenge,
    AuthenticatorSMSChallengeResponseRequest,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-email")
export class AuthenticatorEmailStage extends BaseStage<
    AuthenticatorSMSChallenge,
    AuthenticatorSMSChallengeResponseRequest
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
                        label="${msg("Email")}"
                        required
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.responseErrors || {})["email"]}
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

    render(): TemplateResult {
        return html`<div class="pf-c-login">
            <div class="pf-c-login__container">
                <div class="pf-c-login__main">${this.renderEmailInput()}</div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-email": AuthenticatorEmailStage;
    }
}
