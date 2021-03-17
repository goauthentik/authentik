import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import { BaseStage } from "../base";
import "webcomponent-qr-code";
import "../../../elements/forms/FormElement";
import { showMessage } from "../../../elements/messages/MessageContainer";
import "../../../elements/EmptyState";
import "../../FormStatic";

export interface AuthenticatorTOTPChallenge extends WithUserInfoChallenge {
    config_url: string;
}

@customElement("ak-stage-authenticator-totp")
export class AuthenticatorTOTPStage extends BaseStage {

    @property({ attribute: false })
    challenge?: AuthenticatorTOTPChallenge;

    static get styles(): CSSResult[] {
        return [PFLogin, PFForm, PFFormControl, PFTitle, PFButton];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state
                ?loading="${true}"
                header=${gettext("Loading")}>
            </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" @submit=${(e: Event) => { this.submitForm(e); }}>
                    <ak-form-static class="pf-c-form__group">
                        <div slot="avatar">
                            <img class="pf-c-avatar" src="${this.challenge.pending_user_avatar}" alt="${gettext("User's avatar")}">
                            ${this.challenge.pending_user}
                        </div>
                        <div slot="link">
                            <a href="/flows/-/cancel/">${gettext("Not you?")}</a>
                        </div>
                    </ak-form-static>
                    <input type="hidden" name="otp_uri" value=${this.challenge.config_url} />
                    <ak-form-element>
                        <!-- @ts-ignore -->
                        <qr-code data="${this.challenge.config_url}"></qr-code>
                        <button type="button" class="pf-c-button pf-m-secondary pf-m-progress pf-m-in-progress" @click=${(e: Event) => {
                            e.preventDefault();
                            if (!this.challenge?.config_url) return;
                            navigator.clipboard.writeText(this.challenge?.config_url).then(() => {
                                showMessage({
                                    level_tag: "success",
                                    message: gettext("Successfully copied TOTP Config.")
                                });
                            });
                        }}>
                            <span class="pf-c-button__progress"><i class="fas fa-copy"></i></span>
                            ${gettext("Copy")}
                        </button>
                    </ak-form-element>
                    <ak-form-element
                        label="${gettext("Code")}"
                        ?required="${true}"
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.response_errors || {})["code"]}>
                        <!-- @ts-ignore -->
                        <input type="text"
                            name="code"
                            inputmode="numeric"
                            pattern="[0-9]*"
                            placeholder="${gettext("Please enter your TOTP Code")}"
                            autofocus=""
                            autocomplete="one-time-code"
                            class="pf-c-form-control"
                            required="">
                    </ak-form-element>

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${gettext("Continue")}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                </ul>
            </footer>`;
    }

}
