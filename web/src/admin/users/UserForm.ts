import "#admin/users/GroupSelectModal";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { CodeMirrorMode } from "#elements/CodeMirror";
import { ModelForm } from "#elements/forms/ModelForm";
import { RadioOption } from "#elements/forms/Radio";

import { CoreApi, Group, RbacApi, Role, User, UserTypeEnum } from "@goauthentik/api";

import YAML from "yaml";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const UserTypeOptions: readonly RadioOption<UserTypeEnum>[] = [
    {
        label: msg("Internal"),
        value: UserTypeEnum.Internal,
        default: true,
        description: html`${msg(
            "Company employees with access to the full enterprise feature set.",
        )}`,
    },
    {
        label: msg("External"),
        value: UserTypeEnum.External,
        description: html`${msg(
            "External consultants or B2C customers without access to enterprise features.",
        )}`,
    },
    {
        label: msg("Service account"),
        value: UserTypeEnum.ServiceAccount,
        description: html`${msg("Machine-to-machine authentication or other automations.")}`,
    },
];
@customElement("ak-user-form")
export class UserForm extends ModelForm<User, number> {
    @property({ attribute: false })
    public targetGroup: Group | null = null;

    @property({ attribute: false })
    public targetRole: Role | null = null;

    @property()
    defaultPath: string = "users";

    static get defaultUserAttributes(): { [key: string]: unknown } {
        return {};
    }

    static styles: CSSResult[] = [
        ...super.styles,
        css`
            .pf-c-button.pf-m-control {
                height: 100%;
            }
            .pf-c-form-control {
                height: auto !important;
            }
        `,
    ];

    loadInstance(pk: number): Promise<User> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("User updated.");
        }
        if (this.targetGroup) {
            return msg(str`User created and added to group ${this.targetGroup.name}`);
        }
        if (this.targetRole) {
            return msg(str`User created and added to role ${this.targetRole.name}`);
        }
        return msg("User created.");
    }

    async send(data: User): Promise<User> {
        if (data.attributes === null) {
            data.attributes = UserForm.defaultUserAttributes;
        }
        let user;
        if (this.instance?.pk) {
            user = await new CoreApi(DEFAULT_CONFIG).coreUsersPartialUpdate({
                id: this.instance.pk,
                patchedUserRequest: data,
            });
        } else {
            data.groups = [];
            data.roles = [];
            user = await new CoreApi(DEFAULT_CONFIG).coreUsersCreate({
                userRequest: data,
            });
        }
        if (this.targetGroup) {
            await new CoreApi(DEFAULT_CONFIG).coreGroupsAddUserCreate({
                groupUuid: this.targetGroup.pk,
                userAccountRequest: {
                    pk: user.pk,
                },
            });
        }
        if (this.targetRole) {
            await new RbacApi(DEFAULT_CONFIG).rbacRolesAddUserCreate({
                uuid: this.targetRole.pk,
                userAccountSerializerForRoleRequest: {
                    pk: user.pk,
                },
            });
        }
        return user;
    }

    renderForm(): TemplateResult {
        return html` <ak-text-input
                name="username"
                label=${msg("Username")}
                placeholder=${msg("Type a username for the user...")}
                autocomplete="off"
                value="${ifDefined(this.instance?.username)}"
                input-hint="code"
                required
                maxlength=${150}
                help=${msg(
                    "The user's primary identifier used for authentication. 150 characters or fewer.",
                )}
            ></ak-text-input>

            <ak-text-input
                name="name"
                label=${msg("Display Name")}
                placeholder=${msg("Type an optional display name...")}
                autocomplete="off"
                value="${ifDefined(this.instance?.name)}"
                input-hint="code"
                help=${msg("The user's display name.")}
            ></ak-text-input>

            <ak-radio-input
                label=${msg("User type")}
                required
                name="type"
                .value=${this.instance?.type}
                .options=${[
                    ...UserTypeOptions,
                    ...(this.instance
                        ? [
                              {
                                  label: msg("Internal Service account"),
                                  value: UserTypeEnum.InternalServiceAccount,
                                  disabled: true,
                                  description: html`${msg(
                                      "Managed by authentik and cannot be assigned manually.",
                                  )}`,
                              },
                          ]
                        : []),
                ] satisfies RadioOption<UserTypeEnum>[]}
            >
            </ak-radio-input>
            <ak-text-input
                name="email"
                label=${msg("Email Address")}
                placeholder=${msg("Type an optional email address...")}
                autocomplete="off"
                value="${ifDefined(this.instance?.email)}"
                input-hint="code"
            ></ak-text-input>

            <ak-switch-input
                name="isActive"
                label=${msg("Active")}
                ?checked=${this.instance?.isActive ?? true}
                help=${msg(
                    "Whether this user is active and allowed to authenticate. Setting this to inactive can be used to temporarily disable a user without deleting their account.",
                )}
            >
            </ak-switch-input>

            <ak-text-input
                name="path"
                label=${msg("Path")}
                placeholder=${msg("Type a path for the user...")}
                autocomplete="off"
                value="${this.instance?.path ?? this.defaultPath}"
                input-hint="code"
                required
                .bighelp=${html`<p class="pf-c-form__helper-text">
                        ${msg(
                            "Paths can be used to organize users into folders depending on which source created them or organizational structure.",
                        )}
                    </p>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Paths may not start or end with a slash, but they can contain any other character as path segments. The paths are currently purely used for organization, it does not affect their permissions, group memberships, or anything else.",
                        )}
                    </p>`}
            ></ak-text-input>

            <ak-form-element-horizontal label=${msg("Attributes")} name="attributes">
                <ak-codemirror
                    mode=${CodeMirrorMode.YAML}
                    value="${YAML.stringify(
                        this.instance?.attributes ?? UserForm.defaultUserAttributes,
                    )}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-form": UserForm;
    }
}
