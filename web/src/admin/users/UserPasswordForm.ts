import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";

import { CoreApi, UserPasswordSetRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-password-form")
export class UserPasswordForm extends Form<UserPasswordSetRequest> {
    @property({ type: Number })
    instancePk?: number;

    getSuccessMessage(): string {
        return msg("Successfully updated password.");
    }

    async send(data: UserPasswordSetRequest): Promise<void> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersSetPasswordCreate({
            id: this.instancePk || 0,
            userPasswordSetRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Password")} required name="password">
            <input type="password" value="" class="pf-c-form-control" required />
        </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-password-form": UserPasswordForm;
    }
}
