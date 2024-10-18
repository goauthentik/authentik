import { AKElement } from "@goauthentik/elements/Base.js";
import "@goauthentik/elements/forms/FormElement";

import { msg } from "@lit/localize";
import { html, nothing, render } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-flow-input-password")
export class InputPassword extends AKElement {
    static get styles() {
        return [PFBase, PFInputGroup, PFFormControl, PFButton];
    }

    @property({ type: String, attribute: "input-id" })
    inputId = "ak-stage-password-input";

    @property({ type: String })
    name = "password";

    @property({ type: String })
    label = msg("Password");

    @property({ type: String })
    placeholder = msg("Please enter your password");

    @property({ type: String, attribute: "prefill" })
    passwordPrefill = "";

    @property({ type: Object })
    errors: Record<string, string> = {};

    /**
     * Forwarded to the input tag's aria-invalid attribute, if set
     * @attr
     */
    @property({ type: String })
    invalid?: string;

    @property({ type: Boolean, attribute: "allow-show-password" })
    allowShowPassword = false;

    /**
     * Automatically grab focus after rendering.
     * @attr
     */
    @property({ type: Boolean, attribute: "grab-focus" })
    grabFocus = false;

    timer?: number;

    input?: HTMLInputElement;

    cleanup(): void {
        if (this.timer) {
            console.debug("authentik/stages/password: cleared focus timer");
            window.clearInterval(this.timer);
            this.timer = undefined;
        }
    }

    // Must support both older browsers and shadyDom; we'll keep using this in-line, but it'll still
    // be in the scope of the parent element, not an independent shadowDOM.
    createRenderRoot() {
        return this;
    }

    // State is saved in the DOM, and read from the DOM. Directly affects the DOM,
    // so no `.requestUpdate()` required. Effect is immediately visible.
    togglePasswordVisibility(ev: PointerEvent) {
        const passwordField = this.renderRoot.querySelector(`#${this.inputId}`) as HTMLInputElement;
        ev.stopPropagation();
        ev.preventDefault();

        if (!passwordField) {
            throw new Error("ak-flow-password-input: unable to identify input field");
        }

        passwordField.type = passwordField.type === "password" ? "text" : "password";
        this.renderPasswordVisibilityFeatures(passwordField);
    }

    // In the unlikely event that we want to make "show password" the _default_ behavior, this
    // effect handler is broken out into its own method. The current behavior in the main
    // `.render()` method assumes the field is of type "password." To have this effect, er, take
    // effect, call it in an `.updated()` method.
    renderPasswordVisibilityFeatures(passwordField: HTMLInputElement) {
        const toggleId = `#${this.inputId}-visibility-toggle`;
        const visibilityToggle = this.renderRoot.querySelector(toggleId) as HTMLButtonElement;
        if (!visibilityToggle) {
            return;
        }
        const show = passwordField.type === "password";
        visibilityToggle?.setAttribute(
            "aria-label",
            show ? msg("Show password") : msg("Hide password"),
        );
        visibilityToggle?.querySelector("i")?.remove();
        render(
            show
                ? html`<i class="fas fa-eye" aria-hidden="true"></i>`
                : html`<i class="fas fa-eye-slash" aria-hidden="true"></i>`,
            visibilityToggle,
        );
    }

    renderInput(): HTMLInputElement {
        this.input = document.createElement("input");
        this.input.id = `${this.inputId}`;
        this.input.type = "password";
        this.input.name = this.name;
        this.input.placeholder = this.placeholder;
        this.input.autofocus = true;
        this.input.autocomplete = "current-password";
        this.input.classList.add("pf-c-form-control");
        this.input.required = true;
        this.input.value = this.passwordPrefill ?? "";
        if (this.invalid) {
            this.input.setAttribute("aria-invalid", this.invalid);
        }
        // This is somewhat of a crude way to get autofocus, but in most cases the `autofocus` attribute
        // isn't enough, due to timing within shadow doms and such.

        if (this.grabFocus) {
            this.timer = window.setInterval(() => {
                if (!this.input) {
                    return;
                }
                // Because activeElement behaves differently with shadow dom
                // we need to recursively check
                const rootEl = document.activeElement;
                const isActive = (el: Element | null): boolean => {
                    if (!rootEl) return false;
                    if (!("shadowRoot" in rootEl)) return false;
                    if (rootEl.shadowRoot === null) return false;
                    if (rootEl.shadowRoot.activeElement === el) return true;
                    return isActive(rootEl.shadowRoot.activeElement);
                };
                if (isActive(this.input)) {
                    this.cleanup();
                }
                this.input.focus();
            }, 10);
            console.debug("authentik/stages/password: started focus timer");
        }
        return this.input;
    }

    render() {
        return html` <ak-form-element
            label="${this.label}"
            required
            class="pf-c-form__group"
            .errors=${this.errors}
        >
            <div class="pf-c-input-group">
                ${this.renderInput()}
                ${this.allowShowPassword
                    ? html` <button
                          id="${this.inputId}-visibility-toggle"
                          class="pf-c-button pf-m-control ak-stage-password-toggle-visibility"
                          type="button"
                          aria-label=${msg("Show password")}
                          @click=${(ev: PointerEvent) => this.togglePasswordVisibility(ev)}
                      >
                          <i class="fas fa-eye" aria-hidden="true"></i>
                      </button>`
                    : nothing}
            </div>
        </ak-form-element>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-input-password": InputPassword;
    }
}
