import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";
import { PasswordManagerPrefill } from "@goauthentik/flow/stages/identification/IdentificationStage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html, nothing, render } from "lit";
import { customElement, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { PasswordChallenge, PasswordChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-password")
export class PasswordStage extends BaseStage<PasswordChallenge, PasswordChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFInputGroup, PFForm, PFFormControl, PFButton, PFTitle];
    }

    input?: HTMLInputElement;

    timer?: number;

    hasError(field: string): boolean {
        const errors = (this.challenge?.responseErrors || {})[field];
        return (errors || []).length > 0;
    }

    @query("#ak-stage-password-input")
    passwordField!: HTMLInputElement;

    @query("ak-stage-password-toggle-visibility")
    visibilityToggle!: HTMLButtonElement;

    // State is saved in the DOM, and read from the DOM. Directly affects the DOM,
    // so no `.requestUpdate()` required. Effect is immediately visible.
    togglePasswordVisibility(ev: PointerEvent) {
        ev.stopPropagation();
        ev.preventDefault();
        if (!this.passwordField) {
            return;
        }
        this.passwordField.type = this.passwordField.type === "password" ? "text" : "password";
        this.renderPasswordVisibilityFeatures();
    }

    // In the unlikely event that we want to make "show password" the _default_ behavior, this
    // effect handler is broken out into its own method. The current behavior in the main
    // `.render()` method assumes the field is of type "password." To have this effect, er, take
    // effect, call it in an `.updated()` method.
    renderPasswordVisibilityFeatures() {
        if (!this.visibilityToggle) {
            return;
        }
        const show = this.passwordField.type === "password";
        this.visibilityToggle?.setAttribute(
            "aria-label",
            show ? msg("Show password") : msg("Hide password"),
        );
        this.visibilityToggle?.querySelector("i")?.remove();
        render(
            show
                ? html`<i class="fas fa-eye" aria-hidden="true"></i>`
                : html`<i class="fas fa-eye-slash" aria-hidden="true"></i>`,
            this.visibilityToggle,
        );
    }

    renderInput(): HTMLInputElement {
        this.input = document.createElement("input");
        this.input.id = "ak-stage-password-input";
        this.input.type = "password";
        this.input.name = "password";
        this.input.placeholder = msg("Please enter your password");
        this.input.autofocus = true;
        this.input.autocomplete = "current-password";
        this.input.classList.add("pf-c-form-control");
        this.input.required = true;
        this.input.value = PasswordManagerPrefill.password || "";
        this.input.setAttribute("aria-invalid", this.hasError("password").toString());
        // This is somewhat of a crude way to get autofocus, but in most cases the `autofocus` attribute
        // isn't enough, due to timing within shadow doms and such.
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
        return this.input;
    }

    cleanup(): void {
        if (this.timer) {
            console.debug("authentik/stages/password: cleared focus timer");
            window.clearInterval(this.timer);
            this.timer = undefined;
        }
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
                    <ak-form-static
                        class="pf-c-form__group"
                        userAvatar="${this.challenge.pendingUserAvatar}"
                        user=${this.challenge.pendingUser}
                    >
                        <div slot="link">
                            <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                                >${msg("Not you?")}</a
                            >
                        </div>
                    </ak-form-static>
                    <input
                        name="username"
                        autocomplete="username"
                        type="hidden"
                        value="${this.challenge.pendingUser}"
                    />
                    <ak-form-element
                        label="${msg("Password")}"
                        ?required="${true}"
                        class="pf-c-form__group"
                        .errors=${(this.challenge?.responseErrors || {})["password"]}
                    >
                        <div class="pf-c-input-group">
                            ${this.renderInput()}
                            ${this.challenge.allowShowPassword
                                ? html` <button
                                      class="pf-c-button pf-m-control"
                                      type="button"
                                      id="ak-stage-password-toggle-visibility"
                                      aria-label=${msg("Show password")}
                                      @click=${(ev: PointerEvent) =>
                                          this.togglePasswordVisibility(ev)}
                                  >
                                      <i class="fas fa-eye" aria-hidden="true"></i>
                                  </button>`
                                : nothing}
                        </div>
                    </ak-form-element>

                    ${this.challenge.recoveryUrl
                        ? html`<a href="${this.challenge.recoveryUrl}">
                              ${msg("Forgot password?")}</a
                          >`
                        : ""}

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${msg("Continue")}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
