import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#components/ak-switch-input";
import "#components/ak-number-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { WithLicenseSummary } from "#elements/mixins/license";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import { RenderFlowOption } from "#admin/flows/utils";
import { BaseStageForm } from "#admin/stages/BaseStageForm";
import { BackendCheckboxItems } from "#admin/stages/password/labels";

import {
    BackendsEnum,
    Flow,
    FlowDesignationEnum,
    FlowsApi,
    FlowsInstancesListRequest,
    PasswordStage,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-password-form")
export class PasswordStageForm extends WithLicenseSummary(BaseStageForm<PasswordStage>) {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesPasswordRetrieve({ stageUuid }),
        create: (passwordStageRequest: PasswordStage) =>
            aki(StagesApi).stagesPasswordCreate({ passwordStageRequest }),
        update: (stageUuid: string, passwordStageRequest: PasswordStage) =>
            aki(StagesApi).stagesPasswordUpdate({ stageUuid, passwordStageRequest }),
    };

    isBackendSelected(field: BackendsEnum): boolean {
        if (!this.instance) {
            return true;
        }
        return (
            this.instance.backends.filter((isField) => {
                return field === isField;
            }).length > 0
        );
    }

    protected renderLockoutSettings(): SlottedTemplateResult {
        if (!this.hasEnterpriseLicense) {
            return null;
        }

        return html`<ak-number-input
                label=${msg("Failed attempts before lockout", {
                    id: "password-stage.lockout-threshold.label",
                })}
                required
                name="failedAttemptsBeforeLockout"
                min=${0}
                value="${this.instance?.failedAttemptsBeforeLockout ?? 0}"
                help=${msg(
                    "Lock password login after this many consecutive failed attempts. Failed attempts against LDAP and Kerberos backends are not counted. Set to 0 to disable lockout.",
                    {
                        id: "password-stage.lockout-threshold.description",
                    },
                )}
            ></ak-number-input>
            <ak-switch-input
                name="showLastAttemptWarning"
                label=${msg("Show last-attempt warning", {
                    id: "password-stage.last-attempt-warning.label",
                })}
                ?checked=${this.instance?.showLastAttemptWarning ?? false}
                help=${msg("Show a warning when the user has one password attempt remaining.", {
                    id: "password-stage.last-attempt-warning.description",
                })}
            ></ak-switch-input>
            <ak-text-input
                label=${msg("Last-attempt warning message", {
                    id: "password-stage.last-attempt-warning-message.label",
                })}
                name="lastAttemptWarningMessage"
                value=${this.instance?.lastAttemptWarningMessage ?? ""}
                placeholder=${msg(
                    "You have one password attempt remaining before your account is locked out. If you have forgotten your password, please contact your administrator.",
                    {
                        id: "password-stage.last-attempt-warning-message.placeholder",
                    },
                )}
                help=${msg("Leave blank to use the default last-attempt warning.", {
                    id: "password-stage.last-attempt-warning-message.description",
                })}
            ></ak-text-input>
            <ak-switch-input
                name="showLockoutMessage"
                label=${msg("Show lockout message", {
                    id: "password-stage.lockout-message-toggle.label",
                })}
                ?checked=${this.instance?.showLockoutMessage ?? false}
                help=${msg("Show a message to the user when their account is locked out.", {
                    id: "password-stage.lockout-message-toggle.description",
                })}
            ></ak-switch-input>
            <ak-text-input
                label=${msg("Lockout message", {
                    id: "password-stage.lockout-message.label",
                })}
                name="lockoutMessage"
                placeholder=${msg(
                    "Your account has been locked out due to too many failed attempts. Please contact your administrator.",
                    { id: "password-stage.lockout-message.placeholder" },
                )}
                value="${this.instance?.lockoutMessage ?? ""}"
                help=${msg("Leave blank to use the default lockout message.", {
                    id: "password-stage.lockout-message.description",
                })}
            ></ak-text-input>`;
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`<span>
                ${msg("Validate the user's password against the selected backend(s).")}
            </span>
            <ak-text-input
                label=${msg("Stage Name")}
                required
                name="name"
                value="${this.instance?.name || ""}"
                placeholder=${msg("Type a name for this stage...")}
            ></ak-text-input>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal required name="backends">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "backends",
                                required: true,
                            },
                            msg("Backends"),
                        )}
                        <p class="pf-c-form__helper-text">
                            ${msg("Selection of backends to test the password against.")}
                        </p>

                        <ak-checkbox-group
                            class="user-field-select"
                            .options=${BackendCheckboxItems}
                            .value=${BackendCheckboxItems.map(({ name }) => name).filter((name) =>
                                this.isBackendSelected(name),
                            )}
                        ></ak-checkbox-group>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Configuration Flow")}
                        required
                        name="configureFlow"
                    >
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                    designation: FlowDesignationEnum.StageConfiguration,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const flows = await aki(FlowsApi).flowsInstancesList(args);
                                return flows.results;
                            }}
                            .renderElement=${(flow: Flow): string => {
                                return RenderFlowOption(flow);
                            }}
                            .renderDescription=${(flow: Flow) => flow.name}
                            .value=${(flow?: Flow) => flow?.pk}
                            .selected=${(flow: Flow): boolean => {
                                let selected = this.instance?.configureFlow === flow.pk;

                                if (
                                    !this.instance?.pk &&
                                    !this.instance?.configureFlow &&
                                    flow.slug === "default-password-change"
                                ) {
                                    selected = true;
                                }

                                return selected;
                            }}
                            blankable
                        ></ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used by an authenticated user to configure their password. If empty, user will not be able to change their password.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Failed attempts before cancel")}
                        required
                        name="failedAttemptsBeforeCancel"
                    >
                        <input
                            type="number"
                            value="${this.instance?.failedAttemptsBeforeCancel ?? 5}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "How many failed password attempts are allowed before the flow is canceled. This setting does not deactivate the user.",
                                {
                                    id: "password-stage.failed-attempts-before-cancel.description",
                                },
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    ${this.renderLockoutSettings()}
                    <ak-switch-input
                        name="allowShowPassword"
                        label="Show Password Visibility Toggle Button"
                        ?checked=${this.instance?.allowShowPassword ?? false}
                        help=${msg(
                            "Whether to allow users to toggle password visibility in the password input field.",
                            {
                                id: "password-stage.allow-show-password.description",
                            },
                        )}
                    ></ak-switch-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-password-form": PasswordStageForm;
    }
}
