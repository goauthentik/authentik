import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";

import { CoreApi, UserPasswordSetRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-user-password-form")
export class UserPasswordForm extends Form<UserPasswordSetRequest> {
    //#region Properties

    @property({ type: Number })
    public instancePk?: number;

    @property({ type: String })
    public label = msg("New Password");

    @property({ type: String })
    public placeholder = msg("New Password");

    @property({ type: String })
    public username?: string;

    @property({ type: String })
    public email?: string;

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

    public override getSuccessMessage(): string {
        return msg("Successfully updated password.");
    }

    public override async send(data: UserPasswordSetRequest): Promise<void> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersSetPasswordCreate({
            id: this.instancePk || 0,
            userPasswordSetRequest: data,
        });
    }

    //#region Render

    renderForm(): TemplateResult {
        return html` ${this.username
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

            <ak-form-element-horizontal label=${this.label} required name="password">
                <input
                    type="password"
                    value=""
                    class="pf-c-form-control"
                    required
                    placeholder=${ifDefined(this.placeholder || this.label)}
                    aria-label=${this.label}
                    autocomplete=${ifDefined(this.autocomplete)}
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
