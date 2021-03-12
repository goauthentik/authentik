import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import { COMMON_STYLES } from "../../../common/styles";
import { BaseStage } from "../base";
import "../form";
import "../../../elements/utils/LoadingState";
import { PasswordManagerPrefill } from "../identification/IdentificationStage";

export interface PasswordChallenge extends WithUserInfoChallenge {
    recovery_url?: string;
}

@customElement("ak-stage-password")
export class PasswordStage extends BaseStage {

    @property({attribute: false})
    challenge?: PasswordChallenge;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-loading-state></ak-loading-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" @submit=${(e: Event) => {this.submitForm(e);}}>
                    <div class="pf-c-form__group">
                        <div class="form-control-static">
                            <div class="left">
                                <img class="pf-c-avatar" src="${this.challenge.pending_user_avatar}" alt="${gettext("User's avatar")}">
                                ${this.challenge.pending_user}
                            </div>
                            <div class="right">
                                <a href="/flows/-/cancel/">${gettext("Not you?")}</a>
                            </div>
                        </div>
                    </div>

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
                            required=""
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
