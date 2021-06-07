import { t } from "@lingui/macro";
import { css, CSSResult, customElement, html, TemplateResult } from "lit-element";
import { BaseStage } from "../base";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import AKGlobal from "../../../authentik.css";
import "../../../elements/forms/FormElement";
import "../../../elements/EmptyState";
import { FlowChallengeRequest, IdentificationChallenge, IdentificationChallengeResponseRequest, UILoginButton } from "authentik-api";

export const PasswordManagerPrefill: {
    password: string | undefined;
    totp: string | undefined;
} = {
    password: undefined,
    totp: undefined,
};


@customElement("ak-stage-identification")
export class IdentificationStage extends BaseStage<IdentificationChallenge, IdentificationChallengeResponseRequest> {

    static get styles(): CSSResult[] {
        return [PFBase, PFAlert, PFLogin, PFForm, PFFormControl, PFTitle, PFButton, AKGlobal].concat(
            css`
                /* login page's icons */
                .pf-c-login__main-footer-links-item button {
                    background-color: transparent;
                    border: 0;
                }
                .pf-c-login__main-footer-links-item img {
                    fill: var(--pf-c-login__main-footer-links-item-link-svg--Fill);
                    width: 100px;
                    max-width: var(--pf-c-login__main-footer-links-item-link-svg--Width);
                    height: 100%;
                    max-height: var(--pf-c-login__main-footer-links-item-link-svg--Height);
                }
            `
        );
    }

    firstUpdated(): void {
        const wrapperForm = document.createElement("form");
        document.documentElement.appendChild(wrapperForm);
        // This is a workaround for the fact that we're in a shadow dom
        // adapted from https://github.com/home-assistant/frontend/issues/3133
        const username = document.createElement("input");
        username.setAttribute("type", "text");
        username.setAttribute("name", "username"); // username as name for high compatibility
        username.setAttribute("autocomplete", "username");
        username.onkeyup = (ev: Event) => {
            const el = ev.target as HTMLInputElement;
            (this.shadowRoot || this).querySelectorAll<HTMLInputElement>("input[name=uidField]").forEach(input => {
                input.value = el.value;
                // Because we assume only one input field exists that matches this
                // call focus so the user can press enter
                input.focus();
            });
        };
        wrapperForm.appendChild(username);
        const password = document.createElement("input");
        password.setAttribute("type", "password");
        password.setAttribute("name", "password");
        password.setAttribute("autocomplete", "current-password");
        password.onkeyup = (ev: KeyboardEvent) => {
            if (ev.key == "Enter") {
                this.submitForm(ev);
            }
            const el = ev.target as HTMLInputElement;
            // Because the password field is not actually on this page,
            // and we want to 'prefill' the password for the user,
            // save it globally
            PasswordManagerPrefill.password = el.value;
            // Because password managers fill username, then password,
            // we need to re-focus the uid_field here too
            (this.shadowRoot || this).querySelectorAll<HTMLInputElement>("input[name=uidField]").forEach(input => {
                // Because we assume only one input field exists that matches this
                // call focus so the user can press enter
                input.focus();
            });
        };
        wrapperForm.appendChild(password);
        const totp = document.createElement("input");
        totp.setAttribute("type", "text");
        totp.setAttribute("name", "code");
        totp.setAttribute("autocomplete", "one-time-code");
        totp.onkeyup = (ev: KeyboardEvent) => {
            if (ev.key == "Enter") {
                this.submitForm(ev);
            }
            const el = ev.target as HTMLInputElement;
            // Because the totp field is not actually on this page,
            // and we want to 'prefill' the totp for the user,
            // save it globally
            PasswordManagerPrefill.totp = el.value;
            // Because totp managers fill username, then password, then optionally,
            // we need to re-focus the uid_field here too
            (this.shadowRoot || this).querySelectorAll<HTMLInputElement>("input[name=uidField]").forEach(input => {
                // Because we assume only one input field exists that matches this
                // call focus so the user can press enter
                input.focus();
            });
        };
        wrapperForm.appendChild(totp);
    }

    renderSource(source: UILoginButton): TemplateResult {
        let icon = html`<i class="fas fas fa-share-square" title="${source.name}"></i>`;
        if (source.iconUrl) {
            icon = html`<img src="${source.iconUrl}" alt="${source.name}">`;
        }
        return html`<li class="pf-c-login__main-footer-links-item">
                <button type="button" @click=${() => {
                    if (!this.host) return;
                    this.host.challenge = source.challenge as FlowChallengeRequest;
                }}>
                    ${icon}
                </button>
            </li>`;
    }

    renderFooter(): TemplateResult {
        if (!this.challenge?.enrollUrl && !this.challenge?.recoveryUrl) {
            return html``;
        }
        return html`<div class="pf-c-login__main-footer-band">
                ${this.challenge.enrollUrl ? html`
                <p class="pf-c-login__main-footer-band-item">
                    ${t`Need an account?`}
                    <a id="enroll" href="${this.challenge.enrollUrl}">${t`Sign up.`}</a>
                </p>` : html``}
                ${this.challenge.recoveryUrl ? html`
                <p class="pf-c-login__main-footer-band-item">
                    <a id="recovery" href="${this.challenge.recoveryUrl}">${t`Forgot username or password?`}</a>
                </p>` : html``}
            </div>`;
    }

    renderInput(): TemplateResult {
        let label = "";
        let type = "text";
        if (!this.challenge?.userFields) {
            return html`<p>
                ${t`Select one of the sources below to login.`}
            </p>`;
        }
        if (this.challenge?.userFields === ["email"]) {
            label = t`Email`;
            type = "email";
        } else if (this.challenge?.userFields === ["username"]) {
            label = t`Username`;
        } else {
            label = t`Email or username`;
        }
        return html`<ak-form-element
                label=${label}
                ?required="${true}"
                class="pf-c-form__group"
                .errors=${(this.challenge.responseErrors || {})["uid_field"]}>
                <!-- @ts-ignore -->
                <input type=${type}
                    name="uidField"
                    placeholder="Email or Username"
                    autofocus=""
                    autocomplete="username"
                    class="pf-c-form-control"
                    required>
            </ak-form-element>
            ${this.challenge.passwordFields ? html`
                <ak-form-element
                    label="${t`Password`}"
                    ?required="${true}"
                    class="pf-c-form__group"
                    .errors=${(this.challenge.responseErrors || {})["password"]}>
                    <input type="password"
                        name="password"
                        placeholder="${t`Password`}"
                        autofocus=""
                        autocomplete="current-password"
                        class="pf-c-form-control"
                        required
                        value=${PasswordManagerPrefill.password || ""}>
                </ak-form-element>
            `: html``}
            ${"non_field_errors" in (this.challenge?.responseErrors || {}) ?
                this.renderNonFieldErrors(this.challenge?.responseErrors?.non_field_errors || []) :
                html``}
            <div class="pf-c-form__group pf-m-action">
                <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                    ${this.challenge.primaryAction}
                </button>
            </div>`;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state
                ?loading="${true}"
                header=${t`Loading`}>
            </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" @submit=${(e: Event) => {this.submitForm(e);}}>
                    ${this.challenge.applicationPre ?
                        html`<p>
                            ${t`Login to continue to ${this.challenge.applicationPre}.`}
                        </p>`:
                        html``}
                    ${this.renderInput()}
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
