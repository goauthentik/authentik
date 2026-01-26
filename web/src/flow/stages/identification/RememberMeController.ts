import { getCookie } from "#common/utils";

import type { BaseStage } from "#flow/stages/base";

import {
    ChallengeTypes,
    IdentificationChallenge,
    IdentificationChallengeResponseRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html, nothing, ReactiveController } from "lit";
import { guard } from "lit/directives/guard.js";

export function isValidChallenge(challenge: ChallengeTypes): boolean {
    return !(
        challenge.responseErrors &&
        challenge.responseErrors.non_field_errors &&
        challenge.responseErrors.non_field_errors.find((cre) => cre.code === "invalid")
    );
}

export function canAutoSubmit(
    challenge?: IdentificationChallenge | null,
    usernameField?: HTMLInputElement | null,
): boolean {
    return !!(
        challenge &&
        usernameField?.value &&
        !challenge.passwordFields &&
        !challenge.passwordlessUrl
    );
}

export function isRememberAvailable(challenge?: IdentificationChallenge | null): boolean {
    return !!challenge?.enableRememberMe;
}

export function readLocalSession(): string {
    return (getCookie("authentik_csrf") ?? "").substring(0, 8);
}

type RememberMeHost = BaseStage<IdentificationChallenge, IdentificationChallengeResponseRequest>;

const UsernameStorageKey = "authentik-remember-me-user";
const SessionIDStorageKey = "authentik-remember-me-session";

export function readCachedUsername(): string | null {
    try {
        return localStorage.getItem(UsernameStorageKey);
    } catch (_error: unknown) {
        return null;
    }
}

export function persistCachedUsername(username: string | null): void {
    try {
        if (username) {
            localStorage.setItem(UsernameStorageKey, username);
        } else {
            localStorage.removeItem(UsernameStorageKey);
        }
    } catch (_error: unknown) {
        // Ignore
    }
}

export function readCachedSessionID(): string | null {
    try {
        return localStorage.getItem(SessionIDStorageKey);
    } catch (_error: unknown) {
        return null;
    }
}

export function persistCachedSessionID(sessionID: string | null): void {
    try {
        if (sessionID) {
            localStorage.setItem(SessionIDStorageKey, sessionID);
        } else {
            localStorage.removeItem(SessionIDStorageKey);
        }
    } catch (_error: unknown) {
        // Ignore
    }
}

export class AkRememberMeController implements ReactiveController {
    static styles = [
        css`
            .remember-me-switch {
                display: flex;
                padding-top: var(--pf-global--spacer--sm);
                gap: var(--pf-global--spacer--sm);
            }
        `,
    ];

    constructor(
        protected host: RememberMeHost,
        public initialUsername: string = readCachedUsername() ?? "",
    ) {
        host.addController(this);
    }

    // Record a stable token that we can use between requests to track if we've
    // been here before.  If we can't, clear out the username.
    public hostConnected() {
        const localSession = readLocalSession();
        const sessionID = readCachedSessionID();

        if (localSession && localSession === sessionID) {
            persistCachedUsername(null);
        }

        persistCachedSessionID(localSession);
    }

    get usernameField() {
        return this.host.renderRoot?.querySelector(
            'input[name="uidField"]',
        ) as HTMLInputElement | null;
    }

    get rememberMeToggle() {
        return this.host.renderRoot?.querySelector(
            "#authentik-remember-me",
        ) as HTMLInputElement | null;
    }

    get submitButton() {
        return this.host.renderRoot?.querySelector<HTMLButtonElement>('button[type="submit"]');
    }

    // After the page is updated, if everything is ready to go, do the autosubmit.
    public hostUpdated() {
        if (
            isRememberAvailable(this.host.challenge) &&
            canAutoSubmit(this.host.challenge, this.usernameField)
        ) {
            this.submitButton?.click();
        }
    }

    #keyUpListener = () => {
        if (!this.usernameField || !this.usernameField.value) {
            return;
        }

        persistCachedUsername(this.usernameField.value);
    };

    // When active, save current details and record every keystroke to the username.
    // When inactive, clear all fields and remove keystroke recorder.
    #toggleListener = () => {
        if (!this.rememberMeToggle || !this.rememberMeToggle.checked) {
            persistCachedUsername(null);
            persistCachedSessionID(null);

            this.usernameField?.removeEventListener("keyup", this.#keyUpListener);
            return;
        }

        if (!this.usernameField) {
            return;
        }

        persistCachedUsername(this.usernameField.value);

        persistCachedSessionID(readLocalSession());

        this.usernameField.addEventListener("keyup", this.#keyUpListener);
    };

    render() {
        const { challenge } = this.host;
        const available = isRememberAvailable(challenge);

        return guard([available, this.initialUsername], () => {
            if (!available) {
                return nothing;
            }

            return html`<label class="pf-c-switch remember-me-switch">
                <input
                    class="pf-c-switch__input"
                    id="authentik-remember-me"
                    @click=${this.#toggleListener}
                    type="checkbox"
                    ?checked=${!!this.initialUsername}
                />
                <span class="pf-c-form__label">${msg("Remember me on this device")}</span>
            </label>`;
        });
    }
}
