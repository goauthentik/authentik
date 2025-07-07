import { getCookie } from "@goauthentik/common/utils.js";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { ReactiveController, ReactiveControllerHost } from "lit";

import type { IdentificationStage } from "./IdentificationStage.js";

type RememberMeHost = ReactiveControllerHost & IdentificationStage;

export class AkRememberMeController implements ReactiveController {
    static get styles() {
        return css`
            .remember-me-switch {
                display: inline-block;
                padding-top: 0.25rem;
            }
        `;
    }

    username?: string;

    rememberingUsername: boolean = false;

    constructor(private host: RememberMeHost) {
        this.trackRememberMe = this.trackRememberMe.bind(this);
        this.toggleRememberMe = this.toggleRememberMe.bind(this);
        this.host.addController(this);
    }

    // Record a stable token that we can use between requests to track if we've
    // been here before.  If we can't, clear out the username.
    hostConnected() {
        try {
            const sessionId = localStorage.getItem("authentik-remember-me-session");
            if (!!this.localSession && sessionId === this.localSession) {
                this.username = undefined;
                localStorage?.removeItem("authentik-remember-me-user");
            }
            localStorage?.setItem("authentik-remember-me-session", this.localSession);
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (_e: any) {
            this.username = undefined;
        }
    }

    get localSession() {
        return (getCookie("authentik_csrf") ?? "").substring(0, 8);
    }

    get usernameField() {
        return this.host.renderRoot.querySelector(
            'input[name="uidField"]',
        ) as HTMLInputElement | null;
    }

    get rememberMeToggle() {
        return this.host.renderRoot.querySelector(
            "#authentik-remember-me",
        ) as HTMLInputElement | null;
    }

    get isValidChallenge() {
        return !(
            this.host.challenge.responseErrors &&
            this.host.challenge.responseErrors.non_field_errors &&
            this.host.challenge.responseErrors.non_field_errors.find(
                (cre) => cre.code === "invalid",
            )
        );
    }

    get submitButton() {
        return this.host.renderRoot.querySelector('button[type="submit"]') as HTMLButtonElement;
    }

    get isEnabled() {
        return (
            this.host.challenge !== undefined &&
            this.host.challenge.enableRememberMe &&
            typeof localStorage !== "undefined"
        );
    }

    get canAutoSubmit() {
        return (
            !!this.host.challenge &&
            !!this.username &&
            !!this.usernameField?.value &&
            !this.host.challenge.passwordFields &&
            !this.host.challenge.passwordlessUrl
        );
    }

    // Before the page is updated, try to extract the username from localstorage.
    hostUpdate() {
        if (!this.isEnabled) {
            return;
        }

        try {
            this.username = localStorage.getItem("authentik-remember-me-user") || undefined;
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (_e: any) {
            this.username = undefined;
        }
    }

    // After the page is updated, if everything is ready to go, do the autosubmit.
    hostUpdated() {
        if (this.isEnabled && this.canAutoSubmit) {
            this.submitButton?.click();
        }
    }

    trackRememberMe() {
        if (!this.usernameField || this.usernameField.value === undefined) {
            return;
        }
        this.username = this.usernameField.value;
        localStorage?.setItem("authentik-remember-me-user", this.username);
    }

    // When active, save current details and record every keystroke to the username.
    // When inactive, clear all fields and remove keystroke recorder.
    toggleRememberMe() {
        if (!this.rememberMeToggle || !this.rememberMeToggle.checked) {
            localStorage?.removeItem("authentik-remember-me-user");
            localStorage?.removeItem("authentik-remember-me-session");
            this.username = undefined;
            this.usernameField?.removeEventListener("keyup", this.trackRememberMe);
            return;
        }
        if (!this.usernameField) {
            return;
        }
        localStorage?.setItem("authentik-remember-me-user", this.usernameField.value);
        localStorage?.setItem("authentik-remember-me-session", this.localSession);
        this.usernameField.addEventListener("keyup", this.trackRememberMe);
    }

    render() {
        return this.isEnabled
            ? html` <label class="pf-c-switch remember-me-switch">
                  <input
                      class="pf-c-switch__input"
                      id="authentik-remember-me"
                      @click=${this.toggleRememberMe}
                      type="checkbox"
                      ?checked=${!!this.username}
                  />
                  <span class="pf-c-form__label">${msg("Remember me on this device")}</span>
              </label>`
            : nothing;
    }
}
