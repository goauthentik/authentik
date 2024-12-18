import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import "@goauthentik/flow/components/ak-flow-password-input.js";
import { BaseStage } from "@goauthentik/flow/stages/base";
import { PasswordManagerPrefill } from "@goauthentik/flow/stages/identification/IdentificationStage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PasswordChallenge, PasswordChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-password")
export class PasswordStage extends BaseStage<PasswordChallenge, PasswordChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFInputGroup, PFForm, PFFormControl, PFButton, PFTitle];
    }

    hasError(field: string): boolean {
        const errors = (this.challenge?.responseErrors || {})[field];
        return (errors || []).length > 0;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
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
                    <input
                        name="username"
                        autocomplete="username"
                        type="hidden"
                        value="${this.challenge.pendingUser}"
                    />
                    <ak-flow-input-password
                        label=${msg("Password")}
                        required
                        grab-focus
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.responseErrors || {})["password"]}
                        ?allow-show-password=${this.challenge.allowShowPassword}
                        invalid=${this.hasError("password").toString()}
                        prefill=${PasswordManagerPrefill["password"] ?? ""}
                    ></ak-flow-input-password>

                    ${this.challenge.recoveryUrl
                        ? html`<a href="${this.challenge.recoveryUrl}">
                              ${msg("Forgot password?")}</a
                          >`
                        : ""}

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
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-password": PasswordStage;
    }
}
