import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first, groupBy } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    IdentificationStage,
    SourcesApi,
    Stage,
    StagesApi,
    StagesPasswordListRequest,
    UserFieldsEnum,
} from "@goauthentik/api";

@customElement("ak-stage-identification-form")
export class IdentificationStageForm extends ModelForm<IdentificationStage, string> {
    loadInstance(pk: string): Promise<IdentificationStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesIdentificationRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: IdentificationStage): Promise<IdentificationStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesIdentificationUpdate({
                stageUuid: this.instance.pk || "",
                identificationStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesIdentificationCreate({
                identificationStageRequest: data,
            });
        }
    };

    isUserFieldSelected(field: UserFieldsEnum): boolean {
        return (
            (this.instance?.userFields || []).filter((isField) => {
                return field === isField;
            }).length > 0
        );
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Let the user identify themselves with their username or Email address.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Stage-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`User fields`} name="userFields">
                        <select name="users" class="pf-c-form-control" multiple>
                            <option
                                value=${UserFieldsEnum.Username}
                                ?selected=${this.isUserFieldSelected(UserFieldsEnum.Username)}
                            >
                                ${t`Username`}
                            </option>
                            <option
                                value=${UserFieldsEnum.Email}
                                ?selected=${this.isUserFieldSelected(UserFieldsEnum.Email)}
                            >
                                ${t`Email`}
                            </option>
                            <option
                                value=${UserFieldsEnum.Upn}
                                ?selected=${this.isUserFieldSelected(UserFieldsEnum.Upn)}
                            >
                                ${t`UPN`}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Fields a user can identify themselves with. If no fields are selected, the user will only be able to use sources.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Password stage`} name="passwordStage">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Stage[]> => {
                                const args: StagesPasswordListRequest = {
                                    ordering: "name",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const stages = await new StagesApi(
                                    DEFAULT_CONFIG,
                                ).stagesPasswordList(args);
                                return stages.results;
                            }}
                            .groupBy=${(items: Stage[]) => {
                                return groupBy(items, (stage) => stage.verboseNamePlural);
                            }}
                            .renderElement=${(stage: Stage): string => {
                                return stage.name;
                            }}
                            .value=${(stage: Stage | undefined): string | undefined => {
                                return stage?.pk;
                            }}
                            .selected=${(stage: Stage): boolean => {
                                return stage.pk === this.instance?.passwordStage;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`When selected, a password field is shown on the same page instead of a separate page. This prevents username enumeration attacks.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="caseInsensitiveMatching">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.caseInsensitiveMatching, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${t`Case insensitive matching`}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`When enabled, user fields are matched regardless of their casing.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="showMatchedUser">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.showMatchedUser, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${t`Show matched user`}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`When a valid username/email has been entered, and this option is enabled, the user's username and avatar will be shown. Otherwise, the text that the user entered will be shown.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${t`Source settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Sources`}
                        ?required=${true}
                        name="sources"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${until(
                                new SourcesApi(DEFAULT_CONFIG)
                                    .sourcesAllList({})
                                    .then((sources) => {
                                        return sources.results.map((source) => {
                                            let selected = Array.from(
                                                this.instance?.sources || [],
                                            ).some((su) => {
                                                return su == source.pk;
                                            });
                                            // Creating a new instance, auto-select built-in source
                                            // Only when no other sources exist
                                            if (
                                                !this.instance &&
                                                source.component === "" &&
                                                sources.results.length < 2
                                            ) {
                                                selected = true;
                                            }
                                            return html`<option
                                                value=${ifDefined(source.pk)}
                                                ?selected=${selected}
                                            >
                                                ${source.name}
                                            </option>`;
                                        });
                                    }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Select sources should be shown for users to authenticate with. This only affects web-based sources, not LDAP.`}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${t`Hold control/command to select multiple items.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="showSourceLabels">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.showSourceLabels, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${t`Show sources' labels`}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`By default, only icons are shown for sources. Enable this to show their full names.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header">${t`Flow settings`}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Passwordless flow`}
                        name="passwordlessFlow"
                    >
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                    designation: FlowsInstancesListDesignationEnum.Authentication,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(
                                    args,
                                );
                                return flows.results;
                            }}
                            .renderElement=${(flow: Flow): string => {
                                return RenderFlowOption(flow);
                            }}
                            .renderDescription=${(flow: Flow): TemplateResult => {
                                return html`${flow.name}`;
                            }}
                            .value=${(flow: Flow | undefined): string | undefined => {
                                return flow?.pk;
                            }}
                            .selected=${(flow: Flow): boolean => {
                                return this.instance?.passwordlessFlow == flow.pk;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Optional passwordless flow, which is linked at the bottom of the page. When configured, users can use this flow to authenticate with a WebAuthn authenticator, without entering any details.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Enrollment flow`} name="enrollmentFlow">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                    designation: FlowsInstancesListDesignationEnum.Enrollment,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(
                                    args,
                                );
                                return flows.results;
                            }}
                            .renderElement=${(flow: Flow): string => {
                                return flow.slug;
                            }}
                            .renderDescription=${(flow: Flow): TemplateResult => {
                                return html`${flow.name}`;
                            }}
                            .value=${(flow: Flow | undefined): string | undefined => {
                                return flow?.pk;
                            }}
                            .selected=${(flow: Flow): boolean => {
                                return this.instance?.enrollmentFlow == flow.pk;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Optional enrollment flow, which is linked at the bottom of the page.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Recovery flow`} name="recoveryFlow">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                    designation: FlowsInstancesListDesignationEnum.Recovery,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(
                                    args,
                                );
                                return flows.results;
                            }}
                            .renderElement=${(flow: Flow): string => {
                                return flow.slug;
                            }}
                            .renderDescription=${(flow: Flow): TemplateResult => {
                                return html`${flow.name}`;
                            }}
                            .value=${(flow: Flow | undefined): string | undefined => {
                                return flow?.pk;
                            }}
                            .selected=${(flow: Flow): boolean => {
                                return this.instance?.recoveryFlow == flow.pk;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Optional recovery flow, which is linked at the bottom of the page.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
