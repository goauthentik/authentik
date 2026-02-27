import "#elements/Divider";
import "#elements/EmptyState";
import "#flow/components/ak-flow-card";
import "#flow/components/ak-flow-password-input";
import "#flow/stages/captcha/CaptchaStage";

import {
    isConditionalMediationAvailable,
    transformAssertionForServer,
    transformCredentialRequestOptions,
} from "#common/helpers/webauthn";

import { AKFormErrors } from "#components/ak-field-errors";
import { AKLabel } from "#components/ak-label";

import { renderSourceIcon } from "#admin/sources/utils";

import { BaseStage } from "#flow/stages/base";
import { AkRememberMeController } from "#flow/stages/identification/RememberMeController";
import Styles from "#flow/stages/identification/styles.css";

import {
    CaptchaChallenge,
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
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";
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
    static styles: CSSResult[] = [
        PFAlert,
        PFInputGroup,
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        PFButton,
        ...AkRememberMeController.styles,
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

    private rememberMe = new AkRememberMeController(this);

    //#region State

    @state()
    protected captchaToken = "";

    @state()
    protected captchaRefreshedAt = new Date();

    @state()
    protected captchaLoaded = false;

    #captchaInputRef = createRef<HTMLInputElement>();

    #tokenChangeListener = (token: string) => {
        const input = this.#captchaInputRef.value;

        if (!input) return;

        input.value = token;
    };

    #captchaLoadListener = () => {
        this.captchaLoaded = true;
    };

    // AbortController for conditional WebAuthn request
    #passkeyAbortController: AbortController | null = null;

    //#endregion

    //#region Lifecycle

    public override updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        if (changedProperties.has("challenge") && this.challenge) {
            this.#autoRedirect();
            this.#createHelperForm();
            this.#startConditionalWebAuthn();
        }
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        // Abort any pending conditional WebAuthn request when component is removed
        this.#passkeyAbortController?.abort();
        this.#passkeyAbortController = null;
    }

    //#endregion

    #autoRedirect(): void {
        if (!this.challenge) return;
        // We only want to auto-redirect to a source if there's only one source.
        if (this.challenge.sources?.length !== 1) return;

        // And we also only do an auto-redirect if no user fields are select
        // meaning that without the auto-redirect the user would only have the option
        // to manually click on the source button
        if ((this.challenge.userFields || []).length !== 0) return;

        // We also don't want to auto-redirect if there's a passwordless URL configured
        if (this.challenge.passwordlessUrl) return;

        const source = this.challenge.sources[0];
        this.host.challenge = source.challenge;
    }

    /**
     * Start a conditional WebAuthn request for passkey autofill.
     * This allows users to select a passkey from the browser's autofill dropdown.
     */
    async #startConditionalWebAuthn(): Promise<void> {
        // Check if passkey challenge is provided
        // Note: passkeyChallenge is added dynamically and may not be in the generated types yet
        const passkeyChallenge = (
            this.challenge as IdentificationChallenge & {
                passkeyChallenge?: PublicKeyCredentialRequestOptions;
            }
        )?.passkeyChallenge;

        if (!passkeyChallenge) {
            return;
        }

        // Check if browser supports conditional mediation
        const isAvailable = await isConditionalMediationAvailable();
        if (!isAvailable) {
            console.debug("authentik/identification: Conditional mediation not available");
            return;
        }

        // Abort any existing request
        this.#passkeyAbortController?.abort();
        this.#passkeyAbortController = new AbortController();

        try {
            const publicKeyOptions = transformCredentialRequestOptions(passkeyChallenge);

            // Start the conditional WebAuthn request
            const credential = (await navigator.credentials.get({
                publicKey: publicKeyOptions,
                mediation: "conditional",
                signal: this.#passkeyAbortController.signal,
            })) as PublicKeyCredential | null;

            if (!credential) {
                console.debug("authentik/identification: No credential returned");
                return;
            }

            // Transform and submit the passkey response
            const transformedCredential = transformAssertionForServer(credential);

            await this.host?.submit(
                {
                    passkey: transformedCredential,
                },
                {
                    invisible: true,
                },
            );
        } catch (error) {
            if (error instanceof Error && error.name === "AbortError") {
                // Request was aborted, this is expected when navigating away
                console.debug("authentik/identification: Conditional WebAuthn aborted");
                return;
            }
            console.warn("authentik/identification: Conditional WebAuthn failed", error);
        }
    }

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
        const captchaInput = this.#captchaInputRef.value;

        if (captchaInput) {
            captchaInput.value = "";
        }

        this.captchaRefreshedAt = new Date();
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

    protected renderCaptcha(captchaChallenge: CaptchaChallenge) {
        return html`
            <div class="captcha-container">
                <ak-stage-captcha
                    .challenge=${captchaChallenge}
                    .onTokenChange=${this.#tokenChangeListener}
                    .onLoad=${this.#captchaLoadListener}
                    .refreshedAt=${this.captchaRefreshedAt}
                    embedded
                >
                </ak-stage-captcha>
                <input
                    aria-hidden="true"
                    class="faux-input"
                    ${ref(this.#captchaInputRef)}
                    name="captchaToken"
                    type="text"
                    required
                    value=""
                />
            </div>
        `;
    }

    protected renderInput(challenge: IdentificationChallenge) {
        const {
            captchaStage,
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

        const { inputID, rememberMe, captchaLoaded } = this;

        const offerRecovery = flowDesignation === FlowDesignationEnum.Recovery;
        const type = fields.length === 1 && fields[0] === UserFieldsEnum.Email ? "email" : "text";
        const label = OR_LIST_FORMATTERS.format(fields.map((f) => UI_FIELDS[f]));
        const username = rememberMe.username ?? pendingUserIdentifier;
        const captchaPending = captchaStage && captchaStage.interactive && !captchaLoaded;

        // When passkey is enabled, add "webauthn" to autocomplete to enable passkey autofill
        const autocomplete: AutoFill = passkeyChallenge ? "username webauthn" : "username";

        return html`${offerRecovery ? this.renderRecoveryMessage() : nothing}
            <div class="pf-c-form__group">
                ${AKLabel({ required: true, htmlFor: inputID }, label)}
                ${this.renderUidField(inputID, type, label, username, autocomplete)}
                ${rememberMe.render()}
                ${AKFormErrors({ errors: challenge.responseErrors?.uid_field })}
            </div>
            ${passwordFields ? this.renderPasswordFields(challenge) : nothing}
            ${this.renderNonFieldErrors()}
            ${captchaStage ? this.renderCaptcha(captchaStage) : nothing}

            <div class="pf-c-form__group ${captchaStage ? "" : "pf-m-action"}">
                <button
                    ?disabled=${captchaPending}
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
