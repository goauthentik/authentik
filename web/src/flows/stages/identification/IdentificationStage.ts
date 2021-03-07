import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { Challenge } from "../../../api";
import { COMMON_STYLES } from "../../../common/styles";
import { BaseStage } from "../base";
import "../form";
import "../../../elements/utils/LoadingState";

export interface IdentificationChallenge extends Challenge {

    input_type: string;
    primary_action: string;
    sources?: UILoginButton[];

    application_pre?: string;

    enroll_url?: string;
    recovery_url?: string;

}

export interface UILoginButton {
    name: string;
    url: string;
    icon_url?: string;
}

@customElement("ak-stage-identification")
export class IdentificationStage extends BaseStage {

    @property({attribute: false})
    challenge?: IdentificationChallenge;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    renderSource(source: UILoginButton): TemplateResult {
        let icon = html`<i class="pf-icon pf-icon-arrow" title="${source.name}"></i>`;
        if (source.icon_url) {
            icon = html`<img src="${source.icon_url}" alt="${source.name}">`;
        }
        return html`<li class="pf-c-login__main-footer-links-item">
                <a href="${source.url}" class="pf-c-login__main-footer-links-item-link">
                    ${icon}
                </a>
            </li>`;
    }

    renderFooter(): TemplateResult {
        if (!this.challenge?.enroll_url && !this.challenge?.recovery_url) {
            return html``;
        }
        return html`<div class="pf-c-login__main-footer-band">
                ${this.challenge.enroll_url ? html`
                <p class="pf-c-login__main-footer-band-item">
                    ${gettext("Need an account?")}
                    <a id="enroll" href="${this.challenge.enroll_url}">${gettext("Sign up.")}</a>
                </p>` : html``}
                ${this.challenge.recovery_url ? html`
                <p class="pf-c-login__main-footer-band-item">
                    ${gettext("Need an account?")}
                    <a id="recovery" href="${this.challenge.recovery_url}">${gettext("Forgot username or password?")}</a>
                </p>` : html``}
            </div>`;
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
                    ${this.challenge.application_pre ?
                        html`<p>
                            ${gettext(`Login to continue to ${this.challenge.application_pre}.`)}
                        </p>`:
                        html``}

                    <ak-form-element
                        label="${gettext("Email or Username")}"
                        ?required="${true}"
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.responseErrors || {})["uid_field"]}>
                        <input type="text"
                            name="uid_field"
                            placeholder="Email or Username"
                            autofocus=""
                            autocomplete="username"
                            class="pf-c-form-control"
                            required="">
                    </ak-form-element>

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${this.challenge.primary_action}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                    ${(this.challenge.sources || []).map((source) => {
                        return this.renderSource(source);
                    })}
                </ul>
                ${this.renderFooter()}
            </footer>`;
    }

}
