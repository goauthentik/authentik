import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first, groupBy } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-switch-input.js";
import "@goauthentik/elements/ak-checkbox-group/ak-checkbox-group.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    FlowsInstancesListDesignationEnum,
    IdentificationStage,
    Stage,
    StagesApi,
    StagesCaptchaListRequest,
    StagesPasswordListRequest,
    UserFieldsEnum,
} from "@goauthentik/api";

import { sourcesProvider, sourcesSelector } from "./IdentificationStageFormHelpers.js";

@customElement("ak-stage-identification-form")
export class IdentificationStageForm extends BaseStageForm<IdentificationStage> {
    static get styles() {
        return [
            ...super.styles,
            css`
                ak-checkbox-group::part(checkbox-group) {
                    padding-top: var(--pf-c-form--m-horizontal__group-label--md--PaddingTop);
                }
            `,
        ];
    }

    loadInstance(pk: string): Promise<IdentificationStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesIdentificationRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: IdentificationStage): Promise<IdentificationStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesIdentificationUpdate({
                stageUuid: this.instance.pk || "",
                identificationStageRequest: data,
            });
        }

        return new StagesApi(DEFAULT_CONFIG).stagesIdentificationCreate({
            identificationStageRequest: data,
        });
    }

    isUserFieldSelected(field: UserFieldsEnum): boolean {
        return (
            (this.instance?.userFields || []).filter((isField) => {
                return field === isField;
            }).length > 0
        );
    }

    renderForm(): TemplateResult {
        const userSelectFields = [
            { name: UserFieldsEnum.Username, label: msg("Username") },
            { name: UserFieldsEnum.Email, label: msg("Email") },
            { name: UserFieldsEnum.Upn, label: msg("UPN") },
        ];

        return html`<span>
                ${msg("Let the user identify themselves with their username or Email address.")}
            </span>
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
                    <ak-form-element-horizontal label=${msg("User fields")} name="userFields">
                        <ak-checkbox-group
                            class="user-field-select"
                            .options=${userSelectFields}
                            .value=${userSelectFields
                                .map(({ name }) => name)
                                .filter((name) => this.isUserFieldSelected(name))}
                        ></ak-checkbox-group>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Fields a user can identify themselves with. If no fields are selected, the user will only be able to use sources.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Password stage")} name="passwordStage">
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
                            .groupBy=${(items: Stage[]) =>
                                groupBy(items, (stage) => stage.verboseNamePlural)}
                            .renderElement=${(stage: Stage): string => stage.name}
                            .value=${(stage: Stage | undefined): string | undefined => stage?.pk}
                            .selected=${(stage: Stage): boolean =>
                                stage.pk === this.instance?.passwordStage}
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When selected, a password field is shown on the same page instead of a separate page. This prevents username enumeration attacks.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Captcha stage")} name="captchaStage">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Stage[]> => {
                                const args: StagesCaptchaListRequest = {
                                    ordering: "name",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const stages = await new StagesApi(
                                    DEFAULT_CONFIG,
                                ).stagesCaptchaList(args);
                                return stages.results;
                            }}
                            .groupBy=${(items: Stage[]) =>
                                groupBy(items, (stage) => stage.verboseNamePlural)}
                            .renderElement=${(stage: Stage): string => stage.name}
                            .value=${(stage: Stage | undefined): string | undefined => stage?.pk}
                            .selected=${(stage: Stage): boolean =>
                                stage.pk === this.instance?.captchaStage}
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When set, adds functionality exactly like a Captcha stage, but baked into the Identification stage.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        name="caseInsensitiveMatching"
                        label=${msg("Case insensitive matching")}
                        ?checked=${first(this.instance?.caseInsensitiveMatching, true)}
                        help=${msg(
                            "When enabled, user fields are matched regardless of their casing.",
                        )}
                    ></ak-switch-input>
                    <ak-switch-input
                        name="pretendUserExists"
                        label=${msg("Pretend user exists")}
                        ?checked=${first(this.instance?.pretendUserExists, true)}
                        help=${msg(
                            "When enabled, the stage will always accept the given user identifier and continue.",
                        )}
                    ></ak-switch-input>
                    <ak-switch-input
                        name="showMatchedUser"
                        label=${msg("Show matched user")}
                        ?checked=${first(this.instance?.showMatchedUser, true)}
                        help=${msg(
                            "When a valid username/email has been entered, and this option is enabled, the user's username and avatar will be shown. Otherwise, the text that the user entered will be shown.",
                        )}
                    ></ak-switch-input>
                    <ak-switch-input
                        name="enableRememberMe"
                        label=${msg('Enable "Remember me on this device"')}
                        ?checked=${this.instance?.enableRememberMe}
                        help=${msg(
                            "When enabled, the user can save their username in a cookie, allowing them to skip directly to entering their password.",
                        )}
                    ></ak-switch-input>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("Source settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Sources")}
                        ?required=${true}
                        name="sources"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${sourcesProvider}
                            .selector=${sourcesSelector(this.instance?.sources)}
                            available-label="${msg("Available Sources")}"
                            selected-label="${msg("Selected Sources")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Select sources should be shown for users to authenticate with. This only affects web-based sources, not LDAP.",
                            )}
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
                            <span class="pf-c-switch__label">${msg("Show sources' labels")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "By default, only icons are shown for sources. Enable this to show their full names.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header">${msg("Flow settings")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Passwordless flow")}
                        name="passwordlessFlow"
                    >
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.passwordlessFlow}
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Optional passwordless flow, which is linked at the bottom of the page. When configured, users can use this flow to authenticate with a WebAuthn authenticator, without entering any details.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enrollment flow")}
                        name="enrollmentFlow"
                    >
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Enrollment}
                            .currentFlow=${this.instance?.enrollmentFlow}
                        ></ak-flow-search>

                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Optional enrollment flow, which is linked at the bottom of the page.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Recovery flow")} name="recoveryFlow">
                        <ak-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Recovery}
                            .currentFlow=${this.instance?.recoveryFlow}
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Optional recovery flow, which is linked at the bottom of the page.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-identification-form": IdentificationStageForm;
    }
}
