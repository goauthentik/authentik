import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";

import { CoreApi, UserPasswordHashSetRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-password-hash-form")
export class UserPasswordHashForm extends Form<UserPasswordHashSetRequest> {
    @property({ type: Number })
    public instancePk?: number;

    public override getSuccessMessage(): string {
        return msg("Successfully updated password.");
    }

    public override async send(data: UserPasswordHashSetRequest): Promise<void> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersSetPasswordHashCreate({
            id: this.instancePk || 0,
            userPasswordHashSetRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Password hash")} required name="passwordHash">
                <input
                    type="text"
                    value=""
                    class="pf-c-form-control"
                    required
                    placeholder=${msg("pbkdf2_sha256$...")}
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Enter a pre-hashed password (e.g. pbkdf2_sha256$iterations$salt$hash).")}
                </p>
            </ak-form-element-horizontal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-password-hash-form": UserPasswordHashForm;
    }
}
