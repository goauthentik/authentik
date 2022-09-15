import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModalForm } from "@goauthentik/elements/forms/ModalForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CoreApi, UserServiceAccountRequest, UserServiceAccountResponse } from "@goauthentik/api";

@customElement("ak-user-service-account")
export class ServiceAccountForm extends Form<UserServiceAccountRequest> {
    @property({ attribute: false })
    result?: UserServiceAccountResponse;

    getSuccessMessage(): string {
        return t`Successfully created user.`;
    }

    send = (data: UserServiceAccountRequest): Promise<UserServiceAccountResponse> => {
        return new CoreApi(DEFAULT_CONFIG)
            .coreUsersServiceAccountCreate({
                userServiceAccountRequest: data,
            })
            .then((result) => {
                this.result = result;
                (this.parentElement as ModalForm).showSubmitButton = false;
                return result;
            });
    };

    resetForm(): void {
        super.resetForm();
        this.result = undefined;
    }

    renderRequestForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Username`} ?required=${true} name="name">
                <input type="text" value="" class="pf-c-form-control" required />
                <p class="pf-c-form__helper-text">
                    ${t`User's primary identifier. 150 characters or fewer.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="createGroup">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${true} />
                    <label class="pf-c-check__label"> ${t`Create group`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`Enabling this toggle will create a group named after the user, with the user as member.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }

    renderResponseForm(): TemplateResult {
        return html`<p>
                ${t`Use the username and password below to authenticate. The password can be retrieved later on the Tokens page.`}
            </p>
            <form class="pf-c-form pf-m-horizontal">
                <ak-form-element-horizontal label=${t`Username`}>
                    <input
                        type="text"
                        readonly
                        value=${ifDefined(this.result?.username)}
                        class="pf-c-form-control"
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${t`Password`}>
                    <input
                        type="text"
                        readonly
                        value=${ifDefined(this.result?.token)}
                        class="pf-c-form-control"
                    />
                    <p class="pf-c-form__helper-text">
                        ${t`Valid for 360 days, after which the password will automatically rotate. You can copy the password from the Token List.`}
                    </p>
                </ak-form-element-horizontal>
            </form>`;
    }

    renderForm(): TemplateResult {
        if (this.result) {
            return this.renderResponseForm();
        }
        return this.renderRequestForm();
    }
}
