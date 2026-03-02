import "#elements/Divider";
import "#elements/EmptyState";
import "#flow/components/ak-flow-card";
import "#flow/components/ak-flow-password-input";
import "#flow/stages/captcha/CaptchaStage";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { renderSourceIcon } from "#admin/sources/utils";

import { BaseStage } from "#flow/stages/base";
import AutoRedirect from "#flow/stages/identification/controllers/AutoRedirectController";
import CaptchaController from "#flow/stages/identification/controllers/CaptchaController";
import RememberMe from "#flow/stages/identification/controllers/RememberMeController";
import WebauthnController from "#flow/stages/identification/controllers/WebauthnController";
import Styles from "#flow/stages/identification/styles.css";

import {
    FlowDesignationEnum,
    IdentificationChallenge,
    IdentificationChallengeResponseRequest,
    LoginChallengeTypes,
    LoginSource,
    UserFieldsEnum,
} from "@goauthentik/api";

import { kebabCase } from "change-case";
import { match } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { html, nothing, PropertyValues, ReactiveControllerHost } from "lit";
import { customElement, property } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

type PasskeyChallenge = Omit<IdentificationChallenge, "passkeyChallenge"> & {
    passkeyChallenge?: PublicKeyCredentialRequestOptions;
};

type IdentificationFooter = Partial<Pick<IdentificationChallenge, "enrollUrl" | "recoveryUrl">>;

export type IdentificationHost = IdentificationStage & ReactiveControllerHost;

type EmptyString = string | null | undefined;

export const PasswordManagerPrefill: {
    password?: string;
    totp?: string;
} = {};

export const OR_LIST_FORMATTERS: Intl.ListFormat = new Intl.ListFormat("default", {
    style: "short",
    type: "disjunction",
});

const UI_FIELDS: { [key: string]: string } = {
    [UserFieldsEnum.Username]: msg("Username"),
    [UserFieldsEnum.Email]: msg("Email"),
    [UserFieldsEnum.Upn]: msg("UPN"),
};

const sortLoginSources = (a: LoginSource, b: LoginSource) =>
    match([!!a.promoted, !!b.promoted])
        .with([true, false], () => -1)
        .with([false, true], () => 1)
        .otherwise(() => 0);

@customElement("ak-stage-identification")
export class IdentificationStage extends BaseStage<
    IdentificationChallenge,
    IdentificationChallengeResponseRequest
> {
    static styles = [
        PFAlert,
        PFInputGroup,
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        PFButton,
        ...RememberMe.styles,
        Styles,
    ];

    /**
     * The ID of the input field.
     *
     * @attr
     */
    @property({ type: String, attribute: "input-id" })
    public inputID = "ak-identifier-input";

    #form?: HTMLFormElement;

    private rememberMe = new RememberMe(this);
    private autoRedirect = new AutoRedirect(this);
    private captcha = new CaptchaController(this);
    private webauthn = new WebauthnController(this);

    //#endregion

    //#region Lifecycle

    constructor() {
        super();
        // We _define and instantiate_ these fields above, then _read_ them here, and that satisfies
        // the lint pass that there are no unused private fields.
        this.addController(this.rememberMe);
        this.addController(this.autoRedirect);
        this.addController(this.captcha);
        this.addController(this.webauthn);
    }

    public override updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);
        if (changedProperties.has("challenge") && this.challenge) {
            this.#createHelperForm();
        }
    }

    //#endregion

    //#region Helper Form

    #createHelperForm(): void {
        const compatMode = "ShadyDOM" in window;
        this.#form = document.createElement("form");
        document.documentElement.appendChild(this.#form);
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
            this.#form.appendChild(username);
        }
        // Only add the password field when we don't already show a password field
        if (!compatMode && !this.challenge?.passwordFields) {
            const password = document.createElement("input");
            password.setAttribute("type", "password");
            password.setAttribute("name", "password");
            password.setAttribute("autocomplete", "current-password");
            password.onkeyup = (event: KeyboardEvent) => {
                if (event.key === "Enter") {
                    event.preventDefault();
                    this.submitForm();
                }

                const el = event.target as HTMLInputElement;
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

            this.#form.appendChild(password);
        }

        const totp = document.createElement("input");

        totp.setAttribute("type", "text");
        totp.setAttribute("name", "code");
        totp.setAttribute("autocomplete", "one-time-code");
        totp.onkeyup = (event: KeyboardEvent) => {
            if (event.key === "Enter") {
                event.preventDefault();
                this.submitForm();
            }

            const el = event.target as HTMLInputElement;
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

        this.#form.appendChild(totp);
    }

    //#endregion

    protected override onSubmitSuccess(): void {
        this.#form?.remove();
    }

    protected override onSubmitFailure(): void {
        this.captcha.onFailure();
    }

    #dispatchChallengeToHost = (challenge: LoginChallengeTypes) => {
        if (!this.host) return;
        this.host.challenge = challenge;
    };

    protected renderRecoveryMessage() {
        return html`
            <p>${msg("Enter the email address or username associated with your account.")}</p>
        `;
    }

    protected renderUidField(
        id: string,
        type: string,
        label: string,
        username: EmptyString,
        autocomplete: string,
    ) {
        return html`<input
            id=${id}
            type=${type}
            name="uidField"
            placeholder=${label}
            autofocus
            autocomplete=${autocomplete}
            spellcheck="false"
            class="pf-c-form-control"
            value=${username ?? ""}
            required
        />`;
    }

    protected renderPasswordFields(challenge: IdentificationChallenge) {
        const { allowShowPassword } = challenge;
        return html`
            <ak-flow-input-password
                label=${msg("Password")}
                input-id="ak-stage-identification-password"
                class="pf-c-form__group"
                .errors=${challenge.responseErrors?.password}
                ?allow-show-password=${allowShowPassword}
                prefill=${PasswordManagerPrefill.password ?? ""}
            ></ak-flow-input-password>
        `;
    }

    protected renderInput(challenge: IdentificationChallenge) {
        const {
            flowDesignation,
            passkeyChallenge,
            passwordFields,
            passwordlessUrl,
            pendingUserIdentifier,
            primaryAction,
            userFields,
        } = challenge as PasskeyChallenge;

        const fields = (userFields || []).sort();
        if (fields.length === 0) {
            return html`<p>${msg("Select one of the options below to continue.")}</p>`;
        }

        const { inputID, rememberMe } = this;

        const offerRecovery = flowDesignation === FlowDesignationEnum.Recovery;
        const type = fields.length === 1 && fields[0] === UserFieldsEnum.Email ? "email" : "text";
        const label = OR_LIST_FORMATTERS.format(fields.map((f) => UI_FIELDS[f]));
        const username = rememberMe.username ?? pendingUserIdentifier;

        // When passkey is enabled, add "webauthn" to autocomplete to enable passkey autofill
        const autocomplete: AutoFill = passkeyChallenge ? "username webauthn" : "username";

        // prettier-ignore
        return html`${offerRecovery ? this.renderRecoveryMessage() : nothing}
            <div class="pf-c-form__group">
                ${AKLabel({ required: true, htmlFor: inputID }, label)}
                ${this.renderUidField(inputID, type, label, username, autocomplete)}
                ${rememberMe.render()}
                ${AKFormErrors({ errors: challenge.responseErrors?.uid_field })}
            </div>
            ${passwordFields ? this.renderPasswordFields(challenge) : nothing}
            ${this.renderNonFieldErrors()} 
            ${this.captcha.render()}
            <div class="pf-c-form__group ${this.captcha.live ? "" : "pf-m-action"}">
                <button
                    ?disabled=${this.captcha.pending}
                    type="submit"
                    class="pf-c-button pf-m-primary pf-m-block"
                >
                    ${primaryAction}
                </button>
            </div>
            ${passwordlessUrl ? html`<ak-divider>${msg("Or")}</ak-divider>` : nothing}`;
    }

    protected renderPrelude(prelude: string) {
        return html`<p>${msg(str`Log in to continue to ${prelude}.`)}</p>`;
    }

    protected renderPasswordlessUrl(url: string) {
        return html`<a
            href=${url}
            class="pf-c-button pf-m-secondary pf-m-block"
            ouiaId="passwordless"
        >
            ${msg("Use a security key")}
        </a> `;
    }

    //#region Render
    protected renderDefaultSource(source: LoginSource, showLabels: boolean) {
        const { name, iconUrl, challenge } = source;

        const icon = renderSourceIcon(name, iconUrl);
        return html`<button
            type="button"
            @click=${() => this.#dispatchChallengeToHost(challenge)}
            part="source-item"
            name=${`source-${kebabCase(name)}`}
            class="pf-c-button source-button"
            aria-label=${msg(str`Continue with ${name}`)}
        >
            <span class="pf-c-button__icon pf-m-start">${icon}</span>
            ${showLabels ? name : ""}
        </button>`;
    }

    protected renderPromotedSource(source: LoginSource) {
        const { name, challenge } = source;

        return html`<button
            type="button"
            @click=${() => this.#dispatchChallengeToHost(challenge)}
            part="source-item source-item-promoted"
            name=${`source-${kebabCase(name)}`}
            class="pf-c-button pf-m-primary pf-m-block source-button source-button-promoted"
            aria-label=${msg(str`Continue with ${name}`)}
        >
            ${msg(str`Continue with ${name}`)}
        </button>`;
    }

    protected renderLoginSource(source: LoginSource, showLabels: boolean) {
        return source.promoted
            ? this.renderPromotedSource(source)
            : this.renderDefaultSource(source, showLabels);
    }

    protected renderLoginSources(sources: LoginSource[], showLabels: boolean) {
        return html`<fieldset
            slot="footer"
            part="source-list"
            role="group"
            name="login-sources"
            class="pf-c-form__group"
        >
            <legend class="sr-only">${msg("Login sources")}</legend>
            ${repeat(
                [...sources].sort(sortLoginSources),
                (source, idx) => source.name + idx,
                (source) => this.renderLoginSource(source, showLabels),
            )}
        </fieldset> `;
    }

    protected renderIdentificationStage(challenge: IdentificationChallenge) {
        const { applicationPre, passwordlessUrl, showSourceLabels, sources = [] } = challenge;

        return html`
            <form class="pf-c-form" @submit=${this.submitForm}>
                ${applicationPre ? this.renderPrelude(applicationPre) : nothing}
                ${this.renderInput(challenge)}
                ${passwordlessUrl ? this.renderPasswordlessUrl(passwordlessUrl) : nothing}
            </form>
            ${sources.length ? this.renderLoginSources(sources, showSourceLabels) : nothing}
        `;
    }

    protected renderFooter({ enrollUrl, recoveryUrl }: IdentificationFooter) {
        if (!(enrollUrl || recoveryUrl)) {
            return nothing;
        }

        return html`<fieldset
            slot="footer-band"
            part="additional-actions"
            class="pf-c-login__main-footer-band"
        >
            <legend class="sr-only">${msg("Additional actions")}</legend>
            ${enrollUrl
                ? html`<div class="pf-c-login__main-footer-band-item">
                      ${msg("Need an account?")}
                      <a href="${enrollUrl}" ouiaId="enroll">${msg("Sign up.")}</a>
                  </div>`
                : nothing}
            ${recoveryUrl
                ? html`<div class="pf-c-login__main-footer-band-item">
                      <a href="${recoveryUrl}" ouiaId="recovery"
                          >${msg("Forgot username or password?")}</a
                      >
                  </div>`
                : nothing}
        </fieldset>`;
    }

    public override render() {
        const { challenge } = this;
        const { enrollUrl, recoveryUrl } = challenge ?? {};
        const hasFooter = !!enrollUrl || !!recoveryUrl;

        return html`<ak-flow-card .challenge=${challenge} part="flow-card">
            ${challenge ? this.renderIdentificationStage(challenge) : nothing}
            ${hasFooter ? this.renderFooter({ enrollUrl, recoveryUrl }) : nothing}
        </ak-flow-card>`;
    }

    //#endregion
}

export default IdentificationStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-identification": IdentificationStage;
    }
}
