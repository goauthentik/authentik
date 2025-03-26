import { renderSourceIcon } from "@goauthentik/admin/sources/utils";
import "@goauthentik/elements/Divider";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/components/ak-flow-password-input.js";
import { BaseStage } from "@goauthentik/flow/stages/base";
import "@goauthentik/flow/stages/captcha/CaptchaStage";

import { msg, str } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    FlowDesignationEnum,
    IdentificationChallenge,
    IdentificationChallengeResponseRequest,
    LoginSource,
    UserFieldsEnum,
} from "@goauthentik/api";

export const PasswordManagerPrefill: {
    password: string | undefined;
    totp: string | undefined;
} = {
    password: undefined,
    totp: undefined,
};

export const OR_LIST_FORMATTERS = new Intl.ListFormat("default", {
    style: "short",
    type: "disjunction",
});

@customElement("ak-stage-identification")
export class IdentificationStage extends BaseStage<
    IdentificationChallenge,
    IdentificationChallengeResponseRequest
> {
    form?: HTMLFormElement;

    @state()
    captchaToken = "";
    @state()
    captchaRefreshedAt = new Date();

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFAlert,
            PFInputGroup,
            PFLogin,
            PFForm,
            PFFormControl,
            PFTitle,
            PFButton,
            /* login page's icons */
            css`
                .pf-c-login__main-footer-links-item button {
                    background-color: transparent;
                    border: 0;
                    display: flex;
                    align-items: stretch;
                }
                .pf-c-login__main-footer-links-item img {
                    fill: var(--pf-c-login__main-footer-links-item-link-svg--Fill);
                    width: 100px;
                    max-width: var(--pf-c-login__main-footer-links-item-link-svg--Width);
                    height: 100%;
                    max-height: var(--pf-c-login__main-footer-links-item-link-svg--Height);
                }
            `,
        ];
    }

    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("challenge") && this.challenge !== undefined) {
            this.autoRedirect();
            this.createHelperForm();
        }
    }

    autoRedirect(): void {
        if (!this.challenge) return;
        // we only want to auto-redirect to a source if there's only one source
        if (this.challenge.sources?.length !== 1) return;
        // and we also only do an auto-redirect if no user fields are select
        // meaning that without the auto-redirect the user would only have the option
        // to manually click on the source button
        if ((this.challenge.userFields || []).length !== 0) return;
        // we also don't want to auto-redirect if there's a passwordless URL configured
        if (this.challenge.passwordlessUrl) return;
        const source = this.challenge.sources[0];
        this.host.challenge = source.challenge;
    }

    createHelperForm(): void {
        const compatMode = "ShadyDOM" in window;
        this.form = document.createElement("form");
        document.documentElement.appendChild(this.form);
        // Only add the additional username input if we're in a shadow dom
        // otherwise it just confuses browsers
        if (!compatMode) {
            // This is a workaround for the fact that we're in a shadow dom
            // adapted from https://github.com/home-assistant/frontend/issues/3133
            const username = document.createElement("input");
            username.setAttribute("type", "text");
            username.setAttribute("name", "username"); // username as name for high compatibility
            username.setAttribute("autocomplete", "username");
            username.onkeyup = (ev: Event) => {
                const el = ev.target as HTMLInputElement;
                (this.shadowRoot || this)
                    .querySelectorAll<HTMLInputElement>("input[name=uidField]")
                    .forEach((input) => {
                        input.value = el.value;
                        // Because we assume only one input field exists that matches this
                        // call focus so the user can press enter
                        input.focus();
                    });
            };
            this.form.appendChild(username);
        }
        // Only add the password field when we don't already show a password field
        if (!compatMode && !this.challenge.passwordFields) {
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
                (this.shadowRoot || this)
                    .querySelectorAll<HTMLInputElement>("input[name=uidField]")
                    .forEach((input) => {
                        // Because we assume only one input field exists that matches this
                        // call focus so the user can press enter
                        input.focus();
                    });
            };
            this.form.appendChild(password);
        }
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
            (this.shadowRoot || this)
                .querySelectorAll<HTMLInputElement>("input[name=uidField]")
                .forEach((input) => {
                    // Because we assume only one input field exists that matches this
                    // call focus so the user can press enter
                    input.focus();
                });
        };
        this.form.appendChild(totp);
    }

    onSubmitSuccess(): void {
        if (this.form) {
            this.form.remove();
        }
    }

    onSubmitFailure(): void {
        this.captchaRefreshedAt = new Date();
    }

    renderSource(source: LoginSource): TemplateResult {
        const icon = renderSourceIcon(source.name, source.iconUrl);
        return html`<li class="pf-c-login__main-footer-links-item">
            <button
                type="button"
                @click=${() => {
                    if (!this.host) return;
                    this.host.challenge = source.challenge;
                }}
                class=${this.challenge.showSourceLabels ? "pf-c-button pf-m-link" : ""}
            >
                <span class="pf-c-button__icon pf-m-start">${icon}</span>
                ${this.challenge.showSourceLabels ? source.name : ""}
            </button>
        </li>`;
    }

    renderFooter() {
        if (!this.challenge?.enrollUrl && !this.challenge?.recoveryUrl) {
            return nothing;
        }
        return html`<div class="pf-c-login__main-footer-band">
            ${this.challenge.enrollUrl
                ? html`<p class="pf-c-login__main-footer-band-item">
                      ${msg("Need an account?")}
                      <a id="enroll" href="${this.challenge.enrollUrl}">${msg("Sign up.")}</a>
                  </p>`
                : nothing}
            ${this.challenge.recoveryUrl
                ? html`<p class="pf-c-login__main-footer-band-item">
                      <a id="recovery" href="${this.challenge.recoveryUrl}"
                          >${msg("Forgot username or password?")}</a
                      >
                  </p>`
                : nothing}
        </div>`;
    }

    renderInput(): TemplateResult {
        let type: "text" | "email" = "text";
        if (!this.challenge?.userFields || this.challenge.userFields.length === 0) {
            return html`<p>${msg("Select one of the options below to continue.")}</p>`;
        }
        const fields = (this.challenge?.userFields || []).sort();
        // Check if the field should be *only* email to set the input type
        if (fields.includes(UserFieldsEnum.Email) && fields.length === 1) {
            type = "email";
        }
        const uiFields: { [key: string]: string } = {
            [UserFieldsEnum.Username]: msg("Username"),
            [UserFieldsEnum.Email]: msg("Email"),
            [UserFieldsEnum.Upn]: msg("UPN"),
        };
        const label = OR_LIST_FORMATTERS.format(fields.map((f) => uiFields[f]));
        return html`${this.challenge.flowDesignation === FlowDesignationEnum.Recovery
                ? html`
                      <p>
                          ${msg(
                              "Enter the email associated with your account, and we'll send you a link to reset your password.",
                          )}
                      </p>
                  `
                : nothing}
            <ak-form-element
                label=${label}
                required
                class="pf-c-form__group"
                .errors=${(this.challenge.responseErrors || {})["uid_field"]}
            >
                <input
                    type=${type}
                    name="uidField"
                    placeholder=${label}
                    autofocus=""
                    autocomplete="username"
                    spellcheck="false"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element>
            ${this.challenge.passwordFields
                ? html`
                      <ak-flow-input-password
                          label=${msg("Password")}
                          inputId="ak-stage-identification-password"
                          required
                          class="pf-c-form__group"
                          .errors=${(this.challenge?.responseErrors || {})["password"]}
                          ?allow-show-password=${this.challenge.allowShowPassword}
                          prefill=${PasswordManagerPrefill["password"] ?? ""}
                      ></ak-flow-input-password>
                  `
                : nothing}
            ${this.renderNonFieldErrors()}
            ${this.challenge.captchaStage
                ? html`
                      <input name="captchaToken" type="hidden" .value="${this.captchaToken}" />
                      <ak-stage-captcha
                          .challenge=${this.challenge.captchaStage}
                          .onTokenChange=${(token: string) => {
                              this.captchaToken = token;
                          }}
                          .refreshedAt=${this.captchaRefreshedAt}
                          embedded
                      ></ak-stage-captcha>
                  `
                : nothing}
            <div class="pf-c-form__group pf-m-action">
                <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                    ${this.challenge.primaryAction}
                </button>
            </div>
            ${this.challenge.passwordlessUrl
                ? html`<ak-divider>${msg("Or")}</ak-divider>`
                : nothing}`;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
                    ${this.challenge.applicationPre
                        ? html`<p>
                              ${msg(str`Login to continue to ${this.challenge.applicationPre}.`)}
                          </p>`
                        : nothing}
                    ${this.renderInput()}
                    ${this.challenge.passwordlessUrl
                        ? html`
                              <div>
                                  <a
                                      href=${this.challenge.passwordlessUrl}
                                      class="pf-c-button pf-m-secondary pf-m-block"
                                  >
                                      ${msg("Use a security key")}
                                  </a>
                              </div>
                          `
                        : nothing}
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-identification": IdentificationStage;
    }
}
