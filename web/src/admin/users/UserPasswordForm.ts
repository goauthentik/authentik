import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/buttons/SpinnerButton";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, UserPasswordSetRequest } from "@goauthentik/api";

@customElement("ak-user-password-form")
export class UserPasswordForm extends Form<UserPasswordSetRequest> {
    @property({ type: Number })
    instancePk?: number;

    getSuccessMessage(): string {
        return t`Successfully updated password.`;
    }

    async send(data: UserPasswordSetRequest): Promise<void> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersSetPasswordCreate({
            id: this.instancePk || 0,
            userPasswordSetRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Password`} ?required=${true} name="password">
                <input type="password" value="" class="pf-c-form-control" required />
            </ak-form-element-horizontal>
        </form>`;
    }
}
