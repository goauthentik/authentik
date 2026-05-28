import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { Form } from "#elements/forms/Form";
import { ifPresent } from "#elements/utils/attributes";
import { FocusTarget } from "#elements/utils/focus";

import { AKLabel } from "#components/ak-label";

import { CoreApi, UserPasswordSetRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-password-form")
export class UserPasswordForm extends Form<UserPasswordSetRequest> {
    public static shadowRootOptions: ShadowRootInit = {
        ...Form.shadowRootOptions,
        delegatesFocus: true,
    };

    public static override verboseName = msg("Password");
    public static override verboseNamePlural = msg("Passwords");
    public static override submittingVerb = msg("Setting");

    protected autofocusTarget = new FocusTarget<HTMLInputElement>();

    public override focus = this.autofocusTarget.focus;

    //#region Properties

    public override submitLabel = msg("Set Password");
    public override successMessage = msg("Successfully updated password.");

    @property({ type: Number })
    public instancePk?: number;

    @property({ type: String })
    public label = msg("New Password");

    @property({ type: String })
    public placeholder = msg("Type a new password...");

    @property({ type: String, useDefault: true })
    public username: string | null = null;

    @property({ type: String, useDefault: true })
    public email: string | null = null;

    public override size = PFSize.Medium;

    /**
     * The autocomplete attribute to use for the password field.
     *
     * Defaults to "off" to **suggest** that the password is not stored in the browser.
     * However, the browser may not necessarily respect this setting.
     *
     * Still, we can at least hint at our preferred behavior...
     */
    public override autocomplete: Exclude<AutoFillBase, ""> = "off";

    //#endregion

    public override connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener("focus", this.autofocusTarget.toEventListener());
    }

    public override firstUpdated(): void {
        requestAnimationFrame(() => {
            this.focus();
        });
    }

    protected override async send(data: UserPasswordSetRequest): Promise<void> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersSetPasswordCreate({
            id: this.instancePk || 0,
            userPasswordSetRequest: data,
        });
    }

    //#region Render

    protected override renderForm(): TemplateResult {
        return html`${this.username
                ? html`<input
                      hidden
                      readonly
                      autocomplete="username"
                      type="text"
                      name="username"
                      value=${this.username}
                  />`
                : nothing}
            ${this.email
                ? html`<input
                      hidden
                      autocomplete="email"
                      readonly
                      type="email"
                      name="email"
                      value=${this.email}
                  />`
                : nothing}

            <ak-form-element-horizontal required name="password">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "password",
                        required: true,
                    },
                    this.label,
                )}
                <input
                    autofocus
                    ${this.autofocusTarget.toRef()}
                    id="password"
                    type="password"
                    value=""
                    class="pf-c-form-control"
                    required
                    placeholder=${ifPresent(this.placeholder || this.label)}
                    autocomplete=${ifPresent(this.autocomplete)}
                />
            </ak-form-element-horizontal>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-password-form": UserPasswordForm;
    }
}
