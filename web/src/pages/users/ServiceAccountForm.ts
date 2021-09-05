import { CoreApi, UserServiceAccountRequest, UserServiceAccountResponse } from "@goauthentik/api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/HorizontalFormElement";
import { Form } from "../../elements/forms/Form";
import { ModalForm } from "../../elements/forms/ModalForm";
import { ifDefined } from "lit-html/directives/if-defined";

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
                    ${t`Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.`}
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
