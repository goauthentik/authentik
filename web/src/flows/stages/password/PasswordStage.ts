import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import AKGlobal from "../../../authentik.css";
import { BaseStage } from "../base";
import "../../../elements/forms/FormElement";
import "../../../elements/EmptyState";
import { PasswordManagerPrefill } from "../identification/IdentificationStage";
import "../../FormStatic";
import { FlowURLManager } from "../../../api/legacy";

export interface PasswordChallenge extends WithUserInfoChallenge {
    recovery_url?: string;
}

@customElement("ak-stage-password")
export class PasswordStage extends BaseStage {

    @property({attribute: false})
    challenge?: PasswordChallenge;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle, AKGlobal];
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
                <form class="pf-c-form" @submit=${(e: Event) => {this.submitForm(e);}}>
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pending_user_avatar}"
                        user=${this.challenge.pending_user}>
                        <div slot="link">
                            <a href="${FlowURLManager.cancel()}">${gettext("Not you?")}</a>
                        </div>
                    </ak-form-static>
                    <input name="username" autocomplete="username" type="hidden" value="${this.challenge.pending_user}">
                    <ak-form-element
                        label="${gettext("Password")}"
                        ?required="${true}"
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.response_errors || {})["password"]}>
                        <input type="password"
                            name="password"
                            placeholder="${gettext("Please enter your password")}"
                            autofocus=""
                            autocomplete="current-password"
                            class="pf-c-form-control"
                            required
                            value=${PasswordManagerPrefill.password || ""}>
                    </ak-form-element>

                    ${this.challenge.recovery_url ?
                        html`<a href="${this.challenge.recovery_url}">
                        ${gettext("Forgot password?")}</a>` : ""}

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
