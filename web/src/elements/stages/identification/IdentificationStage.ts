import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../../common/styles";
import { BaseStage } from "../base";

export interface IdentificationStageArgs {

    input_type: string;
    primary_action: string;
    sources: string[];

    application_pre?: string;

}

@customElement("ak-stage-identification")
export class IdentificationStage extends BaseStage {

    @property({attribute: false})
    args?: IdentificationStageArgs;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
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
                <form class="pf-c-form">
                    ${this.args.application_pre ?
                        html`<p>
                            ${gettext(`Login to continue to ${this.args.application_pre}.`)}
                        </p>`:
                        html``}

                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label" for="uid_field-0">
                            <span class="pf-c-form__label-text">${gettext("Email or Username")}</span>
                            <span class="pf-c-form__label-required" aria-hidden="true">*</span>
                        </label>
                        <input type="text" name="uid_field" placeholder="Email or Username" autofocus autocomplete="username" class="pf-c-form-control" required="" id="id_uid_field">
                    </div>

                    <div class="pf-c-form__group pf-m-action">
                        <button class="pf-c-button pf-m-primary pf-m-block" @click=${(e: Event) => {
                            e.preventDefault();
                            const form = new FormData(this.shadowRoot.querySelector("form"));
                            this.host?.submit(form);
                        }}>
                            ${this.args.primary_action}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                    ${this.args.sources.map(() => {
                        // TODO: source testing
                        // TODO: Placeholder and label for input above
                        return html``;
                        // {% for source in sources %}
                        // <li class="pf-c-login__main-footer-links-item">
                        //     <a href="{{ source.url }}" class="pf-c-login__main-footer-links-item-link">
                        //         {% if source.icon_path %}
                        //         <img src="{% static source.icon_path %}" style="width:24px;" alt="{{ source.name }}">
                        //         {% elif source.icon_url %}
                        //         <img src="icon_url" alt="{{ source.name }}">
                        //         {% else %}
                        //         <i class="pf-icon pf-icon-arrow" title="{{ source.name }}"></i>
                        //         {% endif %}
                        //     </a>
                        // </li>
                        // {% endfor %}
                    })}
                </ul>
                {% if enroll_url or recovery_url %}
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
                {% endif %}
            </footer>`;
    }

}
