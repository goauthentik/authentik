import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import { UserLoginChallenge, UserLoginChallengeResponseRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

@customElement("ak-stage-user-login")
export class PasswordStage extends BaseStage<
    UserLoginChallenge,
    UserLoginChallengeResponseRequest
> {
    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFFormControl,
        PFSpacing,
        PFButton,
        PFTitle,
    ];

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form
                class="pf-c-form"
                @submit=${(event: SubmitEvent) => {
                    event.preventDefault();

                    const rememberMe = typeof event.submitter?.dataset.rememberMe === "string";

                    this.submitForm(event, {
                        rememberMe,
                    });
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
                <div class="pf-c-form__group">
                    <h3 id="header-text" class="pf-c-title pf-m-xl pf-u-mb-xl">
                        ${msg("Stay signed in?")}
                    </h3>
                    <p class="pf-u-mb-sm">
                        ${msg("Select Yes to reduce the number of times you're asked to sign in.")}
                    </p>
                </div>

                <div class="pf-c-form__group pf-m-action">
                    <button type="submit" data-remember-me class="pf-c-button pf-m-primary">
                        ${msg("Yes")}
                    </button>
                    <button type="submit" class="pf-c-button pf-m-secondary">${msg("No")}</button>
                </div>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-user-login": PasswordStage;
    }
}
