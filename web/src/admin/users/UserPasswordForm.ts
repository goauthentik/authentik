import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/buttons/SpinnerButton";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CoreApi, UserPasswordSetRequest } from "@goauthentik/api";

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
                    autocomplete="new-password"
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
