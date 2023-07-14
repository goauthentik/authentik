import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

import { UserLoginChallenge, UserLoginChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-user-login")
export class PasswordStage extends BaseStage<
    UserLoginChallenge,
    UserLoginChallengeResponseRequest
> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFSpacing, PFButton, PFTitle];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form">
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
                            ${msg(
                                "Select Yes to reduce the number of times you're asked to sign in.",
                            )}
                        </p>
                    </div>

                    <div class="pf-c-form__group pf-m-action">
                        <button
                            @click=${(e: Event) => {
                                this.submitForm(e, {
                                    rememberMe: true,
                                });
                            }}
                            class="pf-c-button pf-m-primary"
                        >
                            ${msg("Yes")}
                        </button>
                        <button
                            @click=${(e: Event) => {
                                this.submitForm(e, {
                                    rememberMe: false,
                                });
                            }}
                            class="pf-c-button pf-m-secondary"
                        >
                            ${msg("No")}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
