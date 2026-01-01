import "#components/ak-hidden-text-input";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { dateTimeLocal } from "#common/temporal";

import { Form } from "#elements/forms/Form";
import { ModalForm } from "#elements/forms/ModalForm";

import { AKLabel } from "#components/ak-label";

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
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const EXPIRATION_DURATION = 1000 * 60 ** 2 * 24 * 360; // 360 days

@customElement("ak-user-service-account-form")
export class ServiceAccountForm extends Form<UserServiceAccountRequest> {
    @state()
    protected expiresAt: Date | null = new Date(Date.now() + EXPIRATION_DURATION);

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

    //#region Event Listeners

    #expiringChangeListener = (event: Event) => {
        const expiringElement = event.target as HTMLInputElement;

        this.expiresAt = expiringElement.checked
            ? new Date(Date.now() + EXPIRATION_DURATION)
            : null;
    };

    //#endregion

    //#region Rendering

    renderForm(): TemplateResult {
        return html`<ak-text-input
                name="name"
                label=${msg("Username")}
                placeholder=${msg("Type a username for the user...")}
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

            <ak-switch-input
                name="expiring"
                label=${msg("Expiring")}
                help=${msg(
                    "Whether the token will expire. Upon expiration, the token will be rotated.",
                )}
                @change=${this.#expiringChangeListener}
                ?checked=${this.expiresAt}
            ></ak-switch-input>

            <ak-form-element-horizontal name="expires">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "expiration-date-input",
                    },
                    msg("Expires on"),
                )}

                <input
                    id="expiration-date-input"
                    type="datetime-local"
                    data-type="datetime-local"
                    value=${this.expiresAt ? dateTimeLocal(this.expiresAt) : ""}
                    ?disabled=${!this.expiresAt}
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

    renderFormWrapper(): TemplateResult {
        if (this.result) {
            return this.renderResponseForm();
        }
        return super.renderFormWrapper();
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-service-account-form": ServiceAccountForm;
    }
}
