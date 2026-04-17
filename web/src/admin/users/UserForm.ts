import "#admin/users/ak-user-group-table";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";
import { RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, Group, RbacApi, Role, User, UserTypeEnum } from "@goauthentik/api";

import { match } from "ts-pattern";
import YAML from "yaml";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const USER_ATTRIBUTE_AGENT_OWNER_PK = "goauthentik.io/agent/owner-pk";

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
    #coreAPI = new CoreApi(DEFAULT_CONFIG);
    #rbacAPI = new RbacApi(DEFAULT_CONFIG);

    public static override verboseName = msg("User");
    public static override verboseNamePlural = msg("Users");

    @property({ attribute: false })
    public targetGroup: Group | null = null;

    @property({ attribute: false })
    public targetRole: Role | null = null;

    @property({ type: String, attribute: "default-path" })
    public defaultPath: string = "users";

    @property({ attribute: false })
    public userType: UserTypeEnum | null = null;

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

    protected override loadInstance(pk: number): Promise<User> {
        return this.#coreAPI.coreUsersRetrieve({
            id: pk,
        });
    }

    private get isAgent(): boolean {
        return !!this.instance?.attributes?.[USER_ATTRIBUTE_AGENT_OWNER_PK];
    }

    protected override assignInstance(instance: User): void {
        super.assignInstance(instance);

        if (this.isAgent) {
            this.verboseName = msg("Agent User");
            this.verboseNamePlural = msg("Agent Users");
            return;
        }

        const { verboseName, verboseNamePlural } = match(instance.type)
            .with(UserTypeEnum.Internal, () => ({
                verboseName: msg("Internal User"),
                verboseNamePlural: msg("Internal Users"),
            }))
            .with(UserTypeEnum.External, () => ({
                verboseName: msg("External User"),
                verboseNamePlural: msg("External Users"),
            }))
            .with(UserTypeEnum.ServiceAccount, () => ({
                verboseName: msg("Service Account"),
                verboseNamePlural: msg("Service Accounts"),
            }))
            .otherwise(() => ({
                verboseName: msg("User"),
                verboseNamePlural: msg("Users"),
            }));

        this.verboseName = verboseName;
        this.verboseNamePlural = verboseNamePlural;
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

        if (this.userType) {
            data.type = this.userType;
        }

        let user;

        if (this.instance?.pk) {
            user = await this.#coreAPI.coreUsersPartialUpdate({
                id: this.instance.pk,
                patchedUserRequest: data,
            });
        } else {
            data.groups = [];
            data.roles = [];

            user = await this.#coreAPI.coreUsersCreate({
                userRequest: data,
            });
        }

        if (this.targetGroup) {
            await this.#coreAPI.coreGroupsAddUserCreate({
                groupUuid: this.targetGroup.pk,
                userAccountRequest: {
                    pk: user.pk,
                },
            });
        }

        if (this.targetRole) {
            await this.#rbacAPI.rbacRolesAddUserCreate({
                uuid: this.targetRole.pk,
                userAccountSerializerForRoleRequest: {
                    pk: user.pk,
                },
            });
        }

        return user;
    }

    protected override renderForm(): SlottedTemplateResult {
        const placeholder =
            this.userType === UserTypeEnum.Internal
                ? msg("Type a username for the internal user...")
                : msg("Type a username for the external user...");

        return html`<ak-text-input
                name="username"
                label=${msg("Username")}
                placeholder=${placeholder}
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

            ${this.userType
                ? null
                : this.isAgent
                  ? html`<ak-radio-input
                        label=${msg("User type")}
                        required
                        name="type"
                        .value=${UserTypeEnum.Internal}
                        .options=${[
                            {
                                label: msg("Agent"),
                                value: UserTypeEnum.Internal,
                                disabled: true,
                                description: html`${msg(
                                    "Agent users are managed by their owner and cannot change type.",
                                )}`,
                            },
                        ] satisfies RadioOption<UserTypeEnum>[]}
                    ></ak-radio-input>`
                  : html`<ak-radio-input
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
                    ></ak-radio-input>`}
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
                    mode="yaml"
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
