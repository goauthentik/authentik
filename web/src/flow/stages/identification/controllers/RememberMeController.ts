import { StorageAccessor } from "#common/storage";
import { getCookie } from "#common/utils";

import { SlottedTemplateResult } from "#elements/types";

import type { IdentificationStage } from "#flow/stages/identification/IdentificationStage";

import { msg } from "@lit/localize";
import { css, html, ReactiveController, ReactiveControllerHost } from "lit";

type RememberMeHost = ReactiveControllerHost & IdentificationStage;

export class RememberMeStorage {
    static readonly username = StorageAccessor.local("authentik-remember-me-user");
    static readonly session = StorageAccessor.local("authentik-remember-me-session");
    static reset = () => {
        this.username.delete();
        this.session.delete();
    };
}

/**
 * Remember the user's `username` "on this device."
 *
 * @remarks
 *
 * If enabled by the site configuration, provides a feature to "remember this user on this device."
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
    static readonly styles = [
        css`
            .remember-me-switch {
                display: flex;
                padding-top: var(--pf-global--spacer--sm);
                gap: var(--pf-global--spacer--sm);
            }
        `,
    ];

    public username: string | null = null;

    #trackRememberMe = () => {
        if (!this.#usernameField || this.#usernameField.value === undefined) {
            return;
        }
        this.username = this.#usernameField.value;
        RememberMeStorage.username.write(this.username);
    };

    // When active, save current details and record every keystroke to the username.
    // When inactive, clear all fields and remove keystroke recorder.
    #toggleRememberMe = () => {
        if (!this.#rememberMeToggle || !this.#rememberMeToggle.checked) {
            RememberMeStorage.reset();
            this.username = null;
            this.#usernameField?.removeEventListener("keyup", this.#trackRememberMe);
            return;
        }
        if (!this.#usernameField) {
            return;
        }

        RememberMeStorage.username.write(this.#usernameField.value);
        RememberMeStorage.session.write(this.#localSession);

        this.#usernameField.addEventListener("keyup", this.#trackRememberMe);
    };

    constructor(private host: RememberMeHost) {}

    // Record a stable token that we can use between requests to track if we've
    // been here before.  If we can't, clear out the username.
    public hostConnected() {
        const sessionID = RememberMeStorage.session.read();

        if (this.#localSession && sessionID === this.#localSession) {
            this.username = null;
            RememberMeStorage.username.delete();
        }

        RememberMeStorage.session.write(this.#localSession);
    }

    get #localSession() {
        return (getCookie("authentik_csrf") ?? "").substring(0, 8);
    }

    get #usernameField() {
        return this.host.renderRoot.querySelector(
            'input[name="uidField"]',
        ) as HTMLInputElement | null;
    }

    get #rememberMeToggle() {
        return this.host.renderRoot.querySelector(
            "#authentik-remember-me",
        ) as HTMLInputElement | null;
    }

    get #submitButton() {
        return this.host.renderRoot.querySelector('button[type="submit"]') as HTMLButtonElement;
    }

    get enabled(): boolean {
        return !!(this.host.challenge?.enableRememberMe && localStorage);
    }

    get #canAutoSubmit(): boolean {
        return !!(
            this.host.challenge &&
            this.username &&
            this.#usernameField?.value &&
            !this.host.challenge.passwordFields &&
            !this.host.challenge.passwordlessUrl
        );
    }

    // Before the page is updated, try to extract the username from localstorage.
    public hostUpdate() {
        if (!this.enabled) {
            return;
        }

        this.username = RememberMeStorage.username.read();
    }

    // After the page is updated, if everything is ready to go, do the autosubmit.
    public hostUpdated() {
        if (this.enabled && this.#canAutoSubmit) {
            this.#submitButton?.click();
        }
    }

    public render(): SlottedTemplateResult {
        if (!this.enabled) {
            return null;
        }

        return html`<label class="pf-c-switch remember-me-switch">
            <input
                class="pf-c-switch__input"
                id="authentik-remember-me"
                @click=${this.#toggleRememberMe}
                type="checkbox"
                ?checked=${!!this.username}
            />
            <span class="pf-c-form__label">${msg("Remember me on this device")}</span>
        </label>`;
    }
}

export default RememberMe;
