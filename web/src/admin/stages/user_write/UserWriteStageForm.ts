import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { RadioOption } from "#elements/forms/Radio";

import { AKLabel } from "#components/ak-label";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    CoreApi,
    CoreGroupsListRequest,
    Group,
    StagesApi,
    UserTypeEnum,
    UserWriteStage,
} from "@goauthentik/api";
import { UserCreationModeEnum } from "@goauthentik/api/dist/models/UserCreationModeEnum.js";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-user-write-form")
export class UserWriteStageForm extends BaseStageForm<UserWriteStage> {
    loadInstance(pk: string): Promise<UserWriteStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesUserWriteRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: UserWriteStage): Promise<UserWriteStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserWriteUpdate({
                stageUuid: this.instance.pk || "",
                userWriteStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesUserWriteCreate({
            userWriteStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <div>
                ${msg(
                    `Write any data from the flow's context's 'prompt_data' to the currently pending user. If no user
        is pending, a new user is created, and data is written to them.`,
                )}
            </div>
            <ak-text-input
                autofocus
                label=${msg("Stage Name")}
                placeholder=${msg("Type a stage name...")}
                required
                name="name"
                value="${ifDefined(this.instance?.name || "")}"
            >
            </ak-text-input>
            <ak-form-group open label=${msg("Stage-specific settings")}>
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="userCreationMode">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "userCreationMode",
                            },
                            msg("User creation mode"),
                        )}

                        <ak-radio
                            .options=${[
                                {
                                    label: msg("Never create users"),
                                    value: UserCreationModeEnum.NeverCreate,
                                    description: html`${msg(
                                        "When no user is present in the flow context, the stage will fail.",
                                    )}`,
                                },
                                {
                                    label: msg("Create users when required"),
                                    value: UserCreationModeEnum.CreateWhenRequired,
                                    default: true,
                                    description: html`${msg(
                                        "When no user is present in the the flow context, a new user is created.",
                                    )}`,
                                },
                                {
                                    label: msg("Always create new users"),
                                    value: UserCreationModeEnum.AlwaysCreate,
                                    description: html`${msg(
                                        "Create a new user even if a user is in the flow context.",
                                    )}`,
                                },
                            ]}
                            .value=${this.instance?.userCreationMode}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        name="createUsersAsInactive"
                        label=${msg("Create users as inactive")}
                        ?checked=${this.instance?.createUsersAsInactive ?? true}
                        help=${msg("Mark newly created users as inactive.")}
                    ></ak-switch-input>
                    <ak-radio-input
                        label=${msg("User type")}
                        name="userType"
                        help=${msg("User type used for newly created users.")}
                        .options=${[
                            {
                                label: msg("Internal"),
                                value: UserTypeEnum.Internal,
                                default: true,
                                description: html`${msg(
                                    "Internal users might be users such as company employees, which will get access to the full Enterprise feature set.",
                                )}`,
                            },
                            {
                                label: msg("External"),
                                value: UserTypeEnum.External,
                                description: html`${msg(
                                    "External users might be external consultants or B2C customers. These users don't get access to enterprise features.",
                                )}`,
                            },
                            {
                                label: msg("Service account"),
                                value: UserTypeEnum.ServiceAccount,
                                description: html`${msg(
                                    "Service accounts should be used for machine-to-machine authentication or other automations.",
                                )}`,
                            },
                        ] satisfies RadioOption<UserTypeEnum>[]}
                        .value=${this.instance?.userType}
                    >
                    </ak-radio-input>
                    <ak-form-element-horizontal
                        label=${msg("User path template")}
                        name="userPathTemplate"
                    >
                        <input
                            type="text"
                            value="${this.instance?.userPathTemplate ?? ""}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Path new users will be created under. If left blank, the default path will be used.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Group")} name="createUsersGroup">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Group[]> => {
                                const args: CoreGroupsListRequest = {
                                    ordering: "name",
                                    includeUsers: false,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(
                                    args,
                                );
                                return groups.results;
                            }}
                            .renderElement=${(group: Group): string => {
                                return group.name;
                            }}
                            .value=${(group: Group | undefined): string | undefined => {
                                return group ? group.pk : undefined;
                            }}
                            .selected=${(group: Group): boolean => {
                                return group.pk === this.instance?.createUsersGroup;
                            }}
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Newly created users are added to this group, if a group is selected.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-user-write-form": UserWriteStageForm;
    }
}
