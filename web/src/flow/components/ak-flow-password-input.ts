import { AKElement } from "@goauthentik/elements/Base.js";
import { bound } from "@goauthentik/elements/decorators/bound";
import "@goauthentik/elements/forms/FormElement";
import { isActiveElement } from "@goauthentik/elements/utils/focus";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { Ref, createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * A configuration object for the visibility states of the password input.
 */
interface VisibilityProps {
    icon: string;
    label: string;
}

/**
 * Enum-like object for the visibility states of the password input.
 */
const Visibility = {
    Reveal: {
        icon: "fa-eye",
        label: msg("Show password"),
    },
    Mask: {
        icon: "fa-eye-slash",
        label: msg("Hide password"),
    },
} as const satisfies Record<string, VisibilityProps>;

@customElement("ak-flow-input-password")
export class InputPassword extends AKElement {
    static get styles() {
        return [PFBase, PFInputGroup, PFFormControl, PFButton];
    }

    //#region Properties

    /**
     * The ID of the input field.
     *
     * @attr
     */
    @property({ type: String, attribute: "input-id" })
    inputId = "ak-stage-password-input";

    /**
     * The name of the input field.
     *
     * @attr
     */
    @property({ type: String })
    name = "password";

    /**
     * The label for the input field.
     *
     * @attr
     */
    @property({ type: String })
    label = msg("Password");

    /**
     * The placeholder text for the input field.
     *
     * @attr
     */
    @property({ type: String })
    placeholder = msg("Please enter your password");

    /**
     * The initial value of the input field.
     *
     * @attr
     */
    @property({ type: String, attribute: "prefill" })
    initialValue = "";

    /**
     * The errors for the input field.
     */
    @property({ type: Object })
    errors: Record<string, string> = {};

    /**
     * Forwarded to the input tag's aria-invalid attribute, if set
     * @attr
     */
    @property({ type: String })
    invalid?: string;

    /**
     * Whether to allow the user to toggle the visibility of the password.
     *
     * @attr
     */
    @property({ type: Boolean, attribute: "allow-show-password" })
    allowShowPassword = false;

    /**
     * Whether the password is currently visible.
     *
     * @attr
     */
    @property({ type: Boolean, attribute: "password-visible" })
    passwordVisible = false;

    /**
     * Automatically grab focus after rendering.
     *
     * @attr
     */
    @property({ type: Boolean, attribute: "grab-focus" })
    grabFocus = false;

    //#endregion

    //#region Refs

    inputRef: Ref<HTMLInputElement> = createRef();

    toggleVisibilityRef: Ref<HTMLButtonElement> = createRef();

    //#endregion

    //#region State

    /**
     * Whether the caps lock key is enabled.
     */
    @state()
    capsLock = false;

    //#endregion

    //#region Listeners

    /**
     * Toggle the visibility of the password field.
     *
     * Directly affects the DOM, so no `.requestUpdate()` required. Effect is immediately visible.
     *
     * @param event The event that triggered the visibility toggle.
     */
    @bound
    togglePasswordVisibility(event?: PointerEvent) {
        event?.stopPropagation();
        event?.preventDefault();

        const input = this.inputRef.value;

        if (!input) {
            console.warn("ak-flow-password-input: unable to identify input field");

            return;
        }

        input.type = input.type === "password" ? "text" : "password";

        this.syncVisibilityToggle(input);
    }

    /**
     * Listen for key events, synchronizing the caps lock indicators.
     */
    @bound
    capsLockListener(event: KeyboardEvent) {
        this.capsLock = event.getModifierState("CapsLock");
    }

    //#region Lifecycle

    /**
     * Interval ID for the focus observer.
     *
     * @see {@linkcode observeInputFocus}
     */
    inputFocusIntervalID?: ReturnType<typeof setInterval>;

    /**
     * Periodically attempt to focus the input field until it is focused.
     *
     * This is some-what of a crude way to get autofocus, but in most cases
     * the `autofocus` attribute isn't enough, due to timing within shadow doms and such.
     */
    observeInputFocus(): void {
        if (!this.grabFocus) {
            return;
        }
        this.inputFocusIntervalID = setInterval(() => {
            const input = this.inputRef.value;

            if (!input) return;

            if (isActiveElement(input, document.activeElement)) {
                console.debug("authentik/stages/password: cleared focus observer");
                clearInterval(this.inputFocusIntervalID);
            }

            input.focus();
        }, 10);

        console.debug("authentik/stages/password: started focus observer");
    }

    connectedCallback() {
        super.connectedCallback();

        this.observeInputFocus();

        addEventListener("keydown", this.capsLockListener);
        addEventListener("keyup", this.capsLockListener);
    }

    disconnectedCallback() {
        if (this.inputFocusIntervalID) {
            clearInterval(this.inputFocusIntervalID);
        }

        super.disconnectedCallback();

        removeEventListener("keydown", this.capsLockListener);
        removeEventListener("keyup", this.capsLockListener);
    }

    //#endregion

    //#region Render

    /**
     * Create the render root for the password input.
     *
     * Must support both older browsers and shadyDom; we'll keep using this in-line,
     * but it'll still be in the scope of the parent element, not an independent shadowDOM.
     */
    createRenderRoot() {
        return this;
    }

    /**
     * Render the password visibility toggle button.
     *
     * In the unlikely event that we want to make "show password" the _default_ behavior,
     * this effect handler is broken out into its own method.
     *
     * The current behavior in the main {@linkcode render} method assumes the field is of type "password."
     *
     * To have this effect, er, take effect, call it in an {@linkcode updated} method.
     *
     * @param input The password field to render the visibility features for.
     */
    syncVisibilityToggle(input: HTMLInputElement | undefined = this.inputRef.value): void {
        if (!input) return;

        const toggleElement = this.toggleVisibilityRef.value;

        if (!toggleElement) return;

        const masked = input.type === "password";

        toggleElement.setAttribute(
            "aria-label",
            masked ? Visibility.Reveal.label : Visibility.Mask.label,
        );

        const iconElement = toggleElement.querySelector("i")!;

        iconElement.classList.remove(Visibility.Mask.icon, Visibility.Reveal.icon);
        iconElement.classList.add(masked ? Visibility.Reveal.icon : Visibility.Mask.icon);
    }

    renderVisibilityToggle() {
        if (!this.allowShowPassword) return nothing;

        const { label, icon } = this.passwordVisible ? Visibility.Mask : Visibility.Reveal;

        return html`<button
            ${ref(this.toggleVisibilityRef)}
            aria-label=${label}
            @click=${this.togglePasswordVisibility}
            class="pf-c-button pf-m-control"
            type="button"
        >
            <i class="fas ${icon}" aria-hidden="true"></i>
        </button>`;
    }

    renderHelperText() {
        if (!this.capsLock) return nothing;

        return html`<div
            class="pf-c-form__helper-text"
            id="helper-text-form-caps-lock-helper"
            aria-live="polite"
        >
            <div class="pf-c-helper-text">
                <div class="pf-c-helper-text__item pf-m-warning">
                    <span class="pf-c-helper-text__item-icon">
                        <i class="fas fa-fw fa-exclamation-triangle" aria-hidden="true"></i>
                    </span>

                    <span class="pf-c-helper-text__item-text">${msg("Caps Lock is enabled.")}</span>
                </div>
            </div>
        </div>`;
    }

    render() {
        return html` <ak-form-element
            label="${this.label}"
            required
            class="pf-c-form__group"
            .errors=${this.errors}
        >
            <div class="pf-c-form__group-control">
                <div class="pf-c-input-group">
                    <input
                        type=${this.passwordVisible ? "text" : "password"}
                        id=${this.inputId}
                        name=${this.name}
                        placeholder=${this.placeholder}
                        autocomplete="current-password"
                        class="${classMap({
                            "pf-c-form-control": true,
                            "pf-m-icon": true,
                            "pf-m-caps-lock": this.capsLock,
                        })}"
                        required
                        aria-invalid=${ifDefined(this.invalid)}
                        value=${this.initialValue}
                        ${ref(this.inputRef)}
                    />

                    ${this.renderVisibilityToggle()}
                </div>

                ${this.renderHelperText()}
            </div>
        </ak-form-element>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-input-password": InputPassword;
    }
}
