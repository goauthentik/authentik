import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { BaseStage } from "../base";
import { AuthenticatorValidateStage, AuthenticatorValidateStageChallenge, DeviceChallenge } from "./AuthenticatorValidateStage";
import "../../../elements/forms/FormElement";
import "../../../elements/EmptyState";
import { PasswordManagerPrefill } from "../identification/IdentificationStage";
import "../../FormStatic";

@customElement("ak-stage-authenticator-validate-code")
export class AuthenticatorValidateStageWebCode extends BaseStage {

    @property({ attribute: false })
    challenge?: AuthenticatorValidateStageChallenge;

    @property({ attribute: false })
    deviceChallenge?: DeviceChallenge;

    @property({ type: Boolean })
    showBackButton = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal];
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state
                ?loading="${true}"
                header=${gettext("Loading")}>
            </ak-empty-state>`;
        }
        return html`<div class="pf-c-login__main-body">
            <form class="pf-c-form" @submit=${(e: Event) => { this.submitForm(e); }}>
                <ak-form-static
                    class="pf-c-form__group"
                    userAvatar="${this.challenge.pending_user_avatar}"
                    user=${this.challenge.pending_user}>
                    <div slot="link">
                        <a href="/flows/-/cancel/">${gettext("Not you?")}</a>
                    </div>
                </ak-form-static>
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
                        value="${PasswordManagerPrefill.totp || ""}"
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
                ${this.showBackButton ?
                    html`<li class="pf-c-login__main-footer-links-item">
                        <button class="pf-c-button pf-m-secondary pf-m-block" @click=${() => {
                            if (!this.host) return;
                            (this.host as AuthenticatorValidateStage).selectedDeviceChallenge = undefined;
                        }}>
                            ${gettext("Return to device picker")}
                        </button>
                    </li>`:
                    html``}
            </ul>
        </footer>`;
    }

}
