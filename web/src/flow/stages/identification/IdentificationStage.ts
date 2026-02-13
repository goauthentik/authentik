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
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
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

type IdentificationFooter = Pick<IdentificationChallenge, "enrollUrl" | "recoveryUrl">;

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

    #rememberMe = new AkRememberMeController(this);

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

    public updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        if (changedProperties.has("challenge") && this.challenge) {
            this.#autoRedirect();
            this.#createHelperForm();
            this.#startConditionalWebAuthn();
        }
    }

    disconnectedCallback(): void {
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
        const passkeyChallenge = (this.challenge as PasskeyChallenge)?.passkeyChallenge;
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

    //#region Render

    renderApplicationPre(applicationPre: string) {
        return html`<p>${msg(str`Login to continue to ${applicationPre}.`)}</p>`;
    }

    dispatchChallengeToHost = (challenge: LoginChallengeTypes) => {
        if (!this.host) return;
        this.host.challenge = challenge;
    };

    renderDefaultSource(source: LoginSource, showLabels: boolean) {
        const icon = renderSourceIcon(source.name, source.iconUrl);
        return html`<button
            type="button"
            @click=${() => this.dispatchChallengeToHost(source.challenge)}
            part="source-item"
            name=${`source-${kebabCase(source.name)}`}
            class="pf-c-button source-button"
            aria-label=${msg(str`Continue with ${source.name}`)}
        >
            <span class="pf-c-button__icon pf-m-start">${icon}</span>
            ${showLabels ? source.name : ""}
        </button>`;
    }

    renderPromotedSource(source: LoginSource) {
        return html`<button
            type="button"
            @click=${() => this.dispatchChallengeToHost(source.challenge)}
            part="source-item source-item-promoted"
            name=${`source-${kebabCase(source.name)}`}
            class="pf-c-button pf-m-primary pf-m-block source-button source-button-promoted"
            aria-label=${msg(str`Continue with ${source.name}`)}
        >
            ${msg(str`Continue with ${source.name}`)}
        </button>`;
    }

    renderSource(source: LoginSource, showLabels: boolean) {
        return source.promoted
            ? this.renderPromotedSource(source)
            : this.renderDefaultSource(source, showLabels);
    }

    renderRecoveryPhase() {
        const message = msg(
            "Enter the email associated with your account, and we'll send you a link to reset your password.",
        );
        return html` <p>${message}</p> `;
    }

    renderIdentityInput(challenge: IdentificationChallenge) {
        const fields = (challenge.userFields || []).sort();
        const type =
            fields.includes(UserFieldsEnum.Email) && fields.length === 1 ? "email" : "text";
        const label = OR_LIST_FORMATTERS.format(fields.map((f) => UI_FIELDS[f]));
        const passkeyChallenge = (challenge as PasskeyChallenge)?.passkeyChallenge;
        const autocomplete: AutoFill = passkeyChallenge ? "username webauthn" : "username";

        return html`<div class="pf-c-form__group">
            ${AKLabel({ required: true, htmlFor: this.inputID }, label)}
            <input
                id=${this.inputID}
                type=${type}
                name="uidField"
                placeholder=${label}
                autofocus
                autocomplete=${autocomplete}
                spellcheck="false"
                class="pf-c-form-control"
                value=${this.#rememberMe?.username ?? challenge.pendingUserIdentifier ?? ""}
                required
            />
            ${this.#rememberMe.render()}
            ${AKFormErrors({ errors: challenge.responseErrors?.uid_field })}
        </div>`;
    }

    renderPasswordFields(challenge: IdentificationChallenge) {
        return html`
            <ak-flow-input-password
                label=${msg("Password")}
                input-id="ak-stage-identification-password"
                required
                class="pf-c-form__group"
                .errors=${challenge.responseErrors?.password}
                ?allow-show-password=${challenge.allowShowPassword}
                prefill=${PasswordManagerPrefill.password ?? ""}
            ></ak-flow-input-password>
        `;
    }

    renderCaptchaStage(captchaChallenge: CaptchaChallenge) {
        return html` <div class="captcha-container">
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
        </div>`;
    }

    renderSubmitButton(challenge: IdentificationChallenge) {
        return html` <div class="pf-c-form__group ${challenge.captchaStage ? "" : "pf-m-action"}">
            <button
                ?disabled=${challenge.captchaStage &&
                challenge.captchaStage.interactive &&
                !this.captchaLoaded}
                type="submit"
                class="pf-c-button pf-m-primary pf-m-block"
            >
                ${challenge.primaryAction}
            </button>
        </div>`;
    }

    renderInput(challenge: IdentificationChallenge): TemplateResult {
        if (!challenge.userFields || challenge.userFields.length === 0) {
            return html`<p>${msg("Select one of the options below to continue.")}</p>`;
        }
        const { passwordFields, captchaStage } = challenge;
        const recovery = challenge.flowDesignation === FlowDesignationEnum.Recovery;

        // prettier-ignore
        return html`
            ${recovery ? this.renderRecoveryPhase() : nothing}
            ${this.renderIdentityInput(challenge)}
            ${passwordFields ? this.renderPasswordFields(challenge) : nothing}
            ${this.renderNonFieldErrors()}
            ${captchaStage ? this.renderCaptchaStage(captchaStage) : nothing}
            ${this.renderSubmitButton(challenge)}
        `;
    }

    renderPasswordlessUrl(passwordlessUrl: string) {
        return html`<ak-divider>${msg("Or")}</ak-divider>
            <a
                name="passwordless"
                href=${passwordlessUrl}
                class="pf-c-button pf-m-secondary pf-m-block"
            >
                ${msg("Use a security key")}
            </a> `;
    }

    // These have the same type, and can be supplied out-of-order. Passing them in by name prevents
    // mis-ordering.
    renderFooter({ enrollUrl, recoveryUrl }: IdentificationFooter) {
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
                      <a name="enroll" href="${enrollUrl}">${msg("Sign up.")}</a>
                  </div>`
                : nothing}
            ${recoveryUrl
                ? html`<div class="pf-c-login__main-footer-band-item">
                      <a name="recovery" href="${recoveryUrl}"
                          >${msg("Forgot username or password?")}</a
                      >
                  </div>`
                : nothing}
        </fieldset>`;
    }

    renderLoginSources(sources: LoginSource[], showLabels: boolean) {
        const key = ({ name }: LoginSource, idx: number) => `${name}${idx}`;
        const content = (source: LoginSource) => this.renderSource(source, showLabels);
        const promoted = (a: LoginSource) => !!a.promoted;

        // Sort promoted sources to show up first
        const sortby = (a: LoginSource, b: LoginSource) =>
            match([promoted(a), promoted(b)])
                .with([true, false], () => -1)
                .with([false, true], () => 1)
                .otherwise(() => 0);

        const sortedSources = [...sources].sort(sortby);

        return html`<fieldset
            slot="footer"
            part="source-list"
            role="group"
            name="login-sources"
            class="pf-c-form__group"
        >
            <legend class="sr-only">${msg("Login sources")}</legend>
            ${repeat(sortedSources, key, content)}
        </fieldset> `;
    }

    renderIdentificationStage(challenge: IdentificationChallenge) {
        const {
            passwordlessUrl,
            applicationPre,
            sources,
            showSourceLabels,
            enrollUrl,
            recoveryUrl,
        } = challenge;
        const hasSources = !!sources?.length;
        const hasFooter = !!enrollUrl || !!recoveryUrl;

        // prettier-ignore
        return html`<ak-flow-card .challenge=${challenge} part="flow-card">
            <form class="pf-c-form" @submit=${this.submitForm}>
                ${applicationPre ? this.renderApplicationPre(applicationPre) : nothing}
                ${this.renderInput(challenge)}
                ${passwordlessUrl ? this.renderPasswordlessUrl(passwordlessUrl) : nothing}
            </form>
            ${hasSources ? this.renderLoginSources(sources, showSourceLabels) : nothing}
            ${hasFooter ? this.renderFooter({ enrollUrl, recoveryUrl}) : nothing }
        </ak-flow-card>`;
    }

    render() {
        if (!this.challenge) {
            console.warn("Identification stage called with empty challenge");
            return nothing;
        }

        return this.renderIdentificationStage(this.challenge);
    }

    //#endregion
}

export default IdentificationStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-identification": IdentificationStage;
    }
}
