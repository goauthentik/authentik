import { renderSourceIcon } from "@goauthentik/admin/sources/SourceViewPage";
import "@goauthentik/elements/Divider";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
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

    static get styles(): CSSResult[] {
        return [PFBase, PFAlert, PFLogin, PFForm, PFFormControl, PFTitle, PFButton].concat(
            css`
                /* login page's icons */
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
        );
    }

    firstUpdated(): void {
        this.autoRedirect();
        this.createHelperForm();
    }

    autoRedirect(): void {
        if (!this.challenge) return;
        // we only want to auto-redirect to a source if there's only one source
        if (this.challenge.sources?.length !== 1) return;
        // and we also only do an auto-redirect if no user fields are select
        // meaning that without the auto-redirect the user would only have the option
        // to manually click on the source button
        if ((this.challenge.userFields || []).length !== 0) return;
        const source = this.challenge.sources[0];
        this.host.challenge = source.challenge;
    }

    createHelperForm(): void {
        this.form = document.createElement("form");
        document.documentElement.appendChild(this.form);
        // Only add the additional username input if we're in a shadow dom
        // otherwise it just confuses browsers
        if (!("ShadyDOM" in window)) {
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

    cleanup(): void {
        if (this.form) {
            this.form.remove();
        }
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

    renderFooter(): TemplateResult {
        if (!this.challenge?.enrollUrl && !this.challenge?.recoveryUrl) {
            return html``;
        }
        return html`<div class="pf-c-login__main-footer-band">
            ${this.challenge.enrollUrl
                ? html`<p class="pf-c-login__main-footer-band-item">
                      ${msg("Need an account?")}
                      <a id="enroll" href="${this.challenge.enrollUrl}">${msg("Sign up.")}</a>
                  </p>`
                : html``}
            ${this.challenge.recoveryUrl
                ? html`<p class="pf-c-login__main-footer-band-item">
                      <a id="recovery" href="${this.challenge.recoveryUrl}"
                          >${msg("Forgot username or password?")}</a
                      >
                  </p>`
                : html``}
        </div>`;
    }

    renderInput(): TemplateResult {
        let type: "text" | "email" = "text";
        if (!this.challenge?.userFields || this.challenge.userFields.length === 0) {
            return html`<p>${msg("Select one of the sources below to login.")}</p>`;
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
        return html`<ak-form-element
                label=${label}
                ?required="${true}"
                class="pf-c-form__group"
                .errors=${(this.challenge.responseErrors || {})["uid_field"]}
            >
                <input
                    type=${type}
                    name="uidField"
                    placeholder=${label}
                    autofocus=""
                    autocomplete="username"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element>
            ${this.challenge.passwordFields
                ? html`
                      <ak-form-element
                          label="${msg("Password")}"
                          ?required="${true}"
                          class="pf-c-form__group"
                          .errors=${(this.challenge.responseErrors || {})["password"]}
                      >
                          <input
                              type="password"
                              name="password"
                              placeholder="${msg("Password")}"
                              autocomplete="current-password"
                              class="pf-c-form-control"
                              required
                              value=${PasswordManagerPrefill.password || ""}
                          />
                      </ak-form-element>
                  `
                : html``}
            ${"non_field_errors" in (this.challenge?.responseErrors || {})
                ? this.renderNonFieldErrors(this.challenge?.responseErrors?.non_field_errors || [])
                : html``}
            <div class="pf-c-form__group pf-m-action">
                <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                    ${this.challenge.primaryAction}
                </button>
            </div>
            ${this.challenge.passwordlessUrl
                ? html`<ak-divider>${msg("Or")}</ak-divider>
                      <div>
                          <a
                              href=${this.challenge.passwordlessUrl}
                              class="pf-c-button pf-m-secondary pf-m-block"
                          >
                              ${msg("Use a security key")}
                          </a>
                      </div>`
                : html``}`;
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
                        : html``}
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
