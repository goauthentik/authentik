import "#components/ak-hidden-text-input";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { dateTimeLocal } from "#common/temporal";

import { Form } from "#elements/forms/Form";
import { ModalForm } from "#elements/forms/ModalForm";

import {
    CoreApi,
    Group,
    RbacApi,
    Role,
    UserServiceAccountRequest,
    UserServiceAccountResponse,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref } from "lit/directives/ref.js";

@customElement("ak-user-service-account-form")
export class ServiceAccountForm extends Form<UserServiceAccountRequest> {
    #initialExpirationValue = dateTimeLocal(new Date(Date.now() + 1000 * 60 ** 2 * 24 * 360));

    //#region Refs

    #expiringInputRef = createRef<HTMLInputElement>();
    #expirationDateInputRef = createRef<HTMLInputElement>();

    //#endregion

    //#region Properties

    @property({ attribute: false })
    result: UserServiceAccountResponse | null = null;

    @property({ attribute: false })
    public targetGroup: Group | null = null;

    @property({ attribute: false })
    public targetRole: Role | null = null;

    //#endregion

    getSuccessMessage(): string {
        if (this.targetGroup) {
            return msg(str`Successfully created user and added to group ${this.targetGroup.name}`);
        }
        return msg("Successfully created user.");
    }

    async send(data: UserServiceAccountRequest): Promise<UserServiceAccountResponse> {
        const result = await new CoreApi(DEFAULT_CONFIG).coreUsersServiceAccountCreate({
            userServiceAccountRequest: data,
        });
        this.result = result;
        (this.parentElement as ModalForm).showSubmitButton = false;
        if (this.targetGroup) {
            await new CoreApi(DEFAULT_CONFIG).coreGroupsAddUserCreate({
                groupUuid: this.targetGroup.pk,
                userAccountRequest: {
                    pk: this.result.userPk,
                },
            });
        }
        if (this.targetRole) {
            await new RbacApi(DEFAULT_CONFIG).rbacRolesAddUserCreate({
                uuid: this.targetRole.pk,
                userAccountSerializerForRoleRequest: {
                    pk: this.result.userPk,
                },
            });
        }
        return result;
    }

    reset(): void {
        super.reset();
        this.result = null;
        (this.parentElement as ModalForm).showSubmitButton = true;
    }

    renderForm(): TemplateResult {
        return html`<ak-text-input
                name="name"
                label=${msg("Username")}
                placeholder=${msg("Type a username for the user...")}
                autocomplete="off"
                value=""
                input-hint="code"
                required
                maxlength=${150}
                autofocus
                help=${msg(
                    "The user's primary identifier used for authentication. 150 characters or fewer.",
                )}
            ></ak-text-input>

            <ak-switch-input
                name="createGroup"
                label=${msg("Create group")}
                help=${msg("Create and assign a group with the same name as the user.")}
            >
            </ak-switch-input>

            <ak-form-element-horizontal name="expiring">
                <label class="pf-c-switch">
                    <input
                        ${ref(this.#expiringInputRef)}
                        class="pf-c-switch__input"
                        type="checkbox"
                        checked
                        @change=${this.expiringChangeListener}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Expiring")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Whether the token will expire. Upon expiration, the token will be rotated.",
                    )}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${msg("Expires on")} name="expires">
                <input
                    ${ref(this.#expirationDateInputRef)}
                    type="datetime-local"
                    data-type="datetime-local"
                    value="${this.#initialExpirationValue}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>`;
    }

    renderResponseForm(): TemplateResult {
        return html`<p>
                ${msg(
                    "Use the username and password below to authenticate. The password can be retrieved later on the Tokens page.",
                )}
            </p>
            <form class="pf-c-form pf-m-horizontal">
                <ak-text-input
                    name="name"
                    label=${msg("Username")}
                    autocomplete="off"
                    value=${ifDefined(this.result?.username)}
                    input-hint="code"
                    readonly
                ></ak-text-input>

                <ak-hidden-text-input
                    label=${msg("Password")}
                    value="${this.result?.token ?? ""}"
                    input-hint="code"
                    readonly
                    .help=${msg(
                        "Valid for 360 days, after which the password will automatically rotate. You can copy the password from the Token List.",
                    )}
                >
                </ak-hidden-text-input>
            </form>`;
    }

    expiringChangeListener = () => {
        const expiringElement = this.#expiringInputRef.value;
        const expirationDateElement = this.#expirationDateInputRef.value;

        if (!expiringElement || !expirationDateElement) return;

        expirationDateElement.disabled = !expiringElement.checked;
    };

    renderFormWrapper(): TemplateResult {
        if (this.result) {
            return this.renderResponseForm();
        }
        return super.renderFormWrapper();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-service-account-form": ServiceAccountForm;
    }
}
