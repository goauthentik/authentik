import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../../common/styles";
import { BaseStage } from "../base";

export interface IdentificationStageArgs {

    input_type: string;
    primary_action: string;
    sources: UILoginButton[];

    application_pre?: string;

}

export interface UILoginButton {
    name: string;
    url: string;
    icon_url?: string;
}

@customElement("ak-stage-identification")
export class IdentificationStage extends BaseStage {

    @property({attribute: false})
    args?: IdentificationStageArgs;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    submit(e: Event): void {
        e.preventDefault();
        const form = new FormData(this.shadowRoot?.querySelector("form") || undefined);
        this.host?.submit(form);
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

    render(): TemplateResult {
        if (!this.args) {
            return html`<ak-loading-state></ak-loading-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${gettext("Log in to your account")}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" @submit=${(e) => {this.submit(e)}}>
                    ${this.args.application_pre ?
                        html`<p>
                            ${gettext(`Login to continue to ${this.args.application_pre}.`)}
                        </p>`:
                        html``}

                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label">
                            <span class="pf-c-form__label-text">${gettext("Email or Username")}</span>
                            <span class="pf-c-form__label-required" aria-hidden="true">*</span>
                        </label>
                        <input type="text" name="uid_field" placeholder="Email or Username" autofocus autocomplete="username" class="pf-c-form-control" required="">
                    </div>

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${this.args.primary_action}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                    ${this.args.sources.map((source) => {
                        return this.renderSource(source);
                    })}
                </ul>

                <!--{% if enroll_url or recovery_url %}
                <div class="pf-c-login__main-footer-band">
                    {% if enroll_url %}
                    <p class="pf-c-login__main-footer-band-item">
                        {% trans 'Need an account?' %}
                        <a role="enroll" href="{{ enroll_url }}">{% trans 'Sign up.' %}</a>
                    </p>
                    {% endif %}
                    {% if recovery_url %}
                    <p class="pf-c-login__main-footer-band-item">
                        <a role="recovery" href="{{ recovery_url }}">{% trans 'Forgot username or password?' %}</a>
                    </p>
                    {% endif %}
                </div>
                {% endif %}-->
            </footer>`;
    }

}
