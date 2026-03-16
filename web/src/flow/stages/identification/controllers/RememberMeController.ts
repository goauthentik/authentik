import { getCookie } from "#common/utils";

import type { IdentificationStage } from "#flow/stages/identification/IdentificationStage";

import { msg } from "@lit/localize";
import { css, html, nothing, ReactiveController, ReactiveControllerHost } from "lit";

type RememberMeHost = ReactiveControllerHost & IdentificationStage;

/**
 * Remember the user's `username` "on this device."
 *
 * @remarks
 *
 * If enabled by the site configuration, provides a feature to "remember this use on this device."
 * When active, it will attempt to find the user's claimed identity in the device & domain
 * localstorage.
 *
 * If claimed identity is present: automatically forward the user to the "prove your identity"
 * phase. If not present: record the username as it is typed in, and store it when the user proceeds
 * to the next phase.
 *
 * Uses a "we've been here before during the current session" heuristic to determine if the user
 * came back to this view after reaching the identity proof phase, indicating they pressed the "not
 * you?" link, at which point it begins again to record the username as it is typed in.
 */
export class RememberMe implements ReactiveController {
    static styles = [
        css`
            .remember-me-switch {
                display: flex;
                padding-top: var(--pf-global--spacer--sm);
                gap: var(--pf-global--spacer--sm);
            }
        `,
    ];

    username?: string;

    rememberingUsername: boolean = false;

    trackRememberMe = () => {
        if (!this.usernameField || this.usernameField.value === undefined) {
            return;
        }
        this.username = this.usernameField.value;
        localStorage?.setItem("authentik-remember-me-user", this.username);
    };

    // When active, save current details and record every keystroke to the username.
    // When inactive, clear all fields and remove keystroke recorder.
    toggleRememberMe = () => {
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
    };

    constructor(private host: RememberMeHost) {}

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
            this.host.challenge?.responseErrors &&
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
        return this.host.challenge?.enableRememberMe && typeof localStorage !== "undefined";
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

export default RememberMe;
