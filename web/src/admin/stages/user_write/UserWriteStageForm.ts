import { UserCreationModeEnum } from "@goauthentik/api/dist/models/UserCreationModeEnum";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CoreApi, CoreGroupsListRequest, Group, StagesApi, UserWriteStage } from "@goauthentik/api";

@customElement("ak-stage-user-write-form")
export class UserWriteStageForm extends ModelForm<UserWriteStage, string> {
    loadInstance(pk: string): Promise<UserWriteStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesUserWriteRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
        }
    }

    async send(data: UserWriteStage): Promise<UserWriteStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserWriteUpdate({
                stageUuid: this.instance.pk || "",
                userWriteStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesUserWriteCreate({
                userWriteStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${msg(
                    `Write any data from the flow's context's 'prompt_data' to the currently pending user. If no user
        is pending, a new user is created, and data is written to them.`,
                )}
            </div>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="userCreationMode">
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
                    <ak-form-element-horizontal name="createUsersAsInactive">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.createUsersAsInactive, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Create users as inactive")}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg("Mark newly created users as inactive.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("User path template")}
                        name="userPathTemplate"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.userPathTemplate, "")}"
                            class="pf-c-form-control"
                            required
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
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Newly created users are added to this group, if a group is selected.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
