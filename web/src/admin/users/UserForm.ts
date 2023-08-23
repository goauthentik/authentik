import "@goauthentik/admin/users/GroupSelectModal";
import { UserTypeEnum } from "@goauthentik/api/dist/models/UserTypeEnum";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CoreApi, User } from "@goauthentik/api";

@customElement("ak-user-form")
export class UserForm extends ModelForm<User, number> {
    static get defaultUserAttributes(): { [key: string]: unknown } {
        return {};
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(css`
            .pf-c-button.pf-m-control {
                height: 100%;
            }
            .pf-c-form-control {
                height: auto !important;
            }
        `);
    }

    loadInstance(pk: number): Promise<User> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated user.");
        } else {
            return msg("Successfully created user.");
        }
    }

    async send(data: User): Promise<User> {
        if (data.attributes === null) {
            data.attributes = UserForm.defaultUserAttributes;
        }
        if (this.instance?.pk) {
            return new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                id: this.instance.pk,
                patchedUserRequest: data,
            });
        } else {
            data.groups = [];
            return new CoreApi(DEFAULT_CONFIG).coreUsersCreate({
                userRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Username")} ?required=${true} name="username">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.username)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("User's primary identifier. 150 characters or fewer.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Name")} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">${msg("User's display name.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("User type")} ?required=${true} name="type">
                <ak-radio
                    .options=${[
                        {
                            label: "Internal",
                            value: UserTypeEnum.Internal,
                            default: true,
                            description: html`${msg(
                                "Internal users might be users such as company employees, which will get access to the full Enterprise feature set.",
                            )}`,
                        },
                        {
                            label: "External",
                            value: UserTypeEnum.External,
                            description: html`${msg(
                                "External users might be external consultants or B2C customers. These users don't get access to enterprise features.",
                            )}`,
                        },
                        {
                            label: "Service account",
                            value: UserTypeEnum.ServiceAccount,
                            description: html`${msg(
                                "Service accounts should be used for machine-to-machine authentication or other automations.",
                            )}`,
                        },
                    ]}
                    .value=${this.instance?.type}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Email")} name="email">
                <input
                    type="email"
                    autocomplete="off"
                    value="${ifDefined(this.instance?.email)}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="isActive">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.isActive, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Is active")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Path")} ?required=${true} name="path">
                <input
                    type="text"
                    value="${first(this.instance?.path, "users")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Attributes")}
                ?required=${false}
                name="attributes"
            >
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(
                        first(this.instance?.attributes, UserForm.defaultUserAttributes),
                    )}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
