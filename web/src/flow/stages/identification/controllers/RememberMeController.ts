import { StorageAccessor } from "#common/storage";
import { getCookie } from "#common/utils";

import { ReactiveElementHost } from "#elements/types";

import type { IdentificationStage } from "#flow/stages/identification/IdentificationStage";

import { ConsoleLogger } from "#logger/browser";

import { msg } from "@lit/localize";
import { css, html, ReactiveController } from "lit";
import { createRef, Ref } from "lit-html/directives/ref.js";

export class RememberMeStorage {
    static readonly user = StorageAccessor.local("authentik-remember-me-user");
    static readonly session = StorageAccessor.local("authentik-remember-me-session");
    static reset = () => {
        this.user.delete();
        this.session.delete();
    };
}

function readSessionID() {
    return (getCookie("authentik_csrf") ?? "").substring(0, 8);
}

export interface RememberMeControllerInit {
    pendingUserIdentifier: string | null;
    identificationFieldRef: Ref<HTMLInputElement>;
    passwordFieldRef: Ref<HTMLInputElement> | null;
    identificationFieldID: string;
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
export class RememberMeController implements ReactiveController {
    static readonly styles = [
        css`
            .remember-me-switch {
                display: flex;
                padding-top: var(--pf-global--spacer--sm);
                gap: var(--pf-global--spacer--sm);
            }
        `,
    ];

    //#region Lifecycle

    public readonly identificationFieldRef: Ref<HTMLInputElement>;
    public readonly passwordFieldRef: Ref<HTMLInputElement> | null;
    public readonly defaultChecked: boolean;
    public readonly defaultUserIdentification: string | null;
    public readonly identificationFieldID: string;

    protected logger = ConsoleLogger.prefix("controller/remember-me");
    protected autoSubmitAttempts = 0;
    protected currentSessionID = readSessionID();

    constructor(
        protected host: ReactiveElementHost<IdentificationStage>,
        {
            identificationFieldRef,
            passwordFieldRef,
            identificationFieldID,
        }: RememberMeControllerInit,
    ) {
        this.identificationFieldRef = identificationFieldRef;
        this.passwordFieldRef = passwordFieldRef || null;
        this.identificationFieldID = identificationFieldID;

        const persistedSessionID = RememberMeStorage.session.read();

        if (persistedSessionID && persistedSessionID !== this.currentSessionID) {
            this.logger.debug("Session ID mismatch, clearing remembered username");
            RememberMeStorage.user.delete();
        }

        const persistedUserIdentifier = RememberMeStorage.user.read();

        this.defaultUserIdentification =
            persistedUserIdentifier || this.host.challenge?.pendingUserIdentifier || null;

        this.defaultChecked = !!persistedUserIdentifier;
    }

    // After the page is updated, if everything is ready to go, do the autosubmit.
    public hostUpdated() {
        if (this.canAutoSubmit() && this.autoSubmitAttempts === 0) {
            this.autoSubmitAttempts++;
            this.host.submitForm?.();
        }
    }

    //#region Event Listeners

    #writeFrameID = -1;

    public inputListener = (event: InputEvent) => {
        cancelAnimationFrame(this.#writeFrameID);
        const { value } = event.target as HTMLInputElement;

        this.#writeFrameID = requestAnimationFrame(() => {
            RememberMeStorage.user.write(value);
        });
    };

    //#endregion

    //#region Public API

    /**
     * Toggle the "remember me" feature on or off.
     *
     * When toggled on, the current username is saved to localStorage and will be automatically
     * submitted on future visits. Additionally, every keystroke in the username field will update
     * the stored username.
     *
     * When toggled off, any stored username is cleared from localStorage, and the keystroke listener
     * is removed to stop updating the stored username.
     */
    public toggleChangeListener = (event: Event) => {
        const checkbox = event.target as HTMLInputElement;
        const { usernameField, passwordField } = this;

        if (!checkbox.checked) {
            this.logger.debug("Disabling remember me");

            RememberMeStorage.reset();

            if (usernameField) {
                usernameField.removeEventListener("input", this.inputListener);
                usernameField.focus();
                usernameField.select();
            }

            return;
        }

        if (!usernameField) {
            this.logger.warn("Cannot enable remember me: no username field found");
            return;
        }

        const focusTarget = passwordField && usernameField?.value ? passwordField : usernameField;

        if (focusTarget) {
            focusTarget.focus();
            focusTarget.select();
        }

        this.logger.debug("Enabling remember me for user");

        RememberMeStorage.user.write(usernameField.value);
        RememberMeStorage.session.write(this.currentSessionID);

        usernameField.addEventListener("input", this.inputListener, {
            passive: true,
        });
    };

    /**
     * Determines if the "remember me" feature can be automatically submitted, which requires:
     *
     * - An active challenge.
     * - A stored username from a previous session.
     * - The identifier input field to be present in the DOM.
     * - No password fields or passwordless URL, indicating we can skip directly to the next step.
     */
    public canAutoSubmit(): boolean {
        const { challenge } = this.host;

        if (!challenge) return false;
        if (!challenge.enableRememberMe) return false;

        if (challenge.passwordFields) return false;
        if (challenge.passwordlessUrl) return false;

        if (!this.defaultChecked) return false;
        return !!this.usernameField?.value;
    }

    //#endregion

    //#region Rendering

    protected readonly checkboxRef = createRef<HTMLInputElement>();

    protected get usernameField() {
        return this.identificationFieldRef.value || null;
    }

    protected get passwordField() {
        return this.passwordFieldRef?.value || null;
    }

    protected get checkboxToggle() {
        return this.checkboxRef.value || null;
    }
    public renderToggleInput = () => {
        return html`<label
            class="pf-c-switch remember-me-switch"
            for="authentik-remember-me"
            aria-description=${msg(
                "When enabled, your username will be remembered on this device for future logins.",
            )}
        >
            <input
                class="pf-c-switch__input"
                type="checkbox"
                id="authentik-remember-me"
                @change=${this.toggleChangeListener}
                ?checked=${this.defaultChecked}
            />
            <span class="pf-c-form__label">${msg("Remember me on this device")}</span>
        </label>`;
    };

    //#endregion
}

export default RememberMeController;
