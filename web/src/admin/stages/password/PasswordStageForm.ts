import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { AKLabel } from "#components/ak-label";

import { RenderFlowOption } from "#admin/flows/utils";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

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
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-password-form")
export class PasswordStageForm extends BaseStageForm<PasswordStage> {
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

    protected override renderForm(): TemplateResult {
        const backends = [
            {
                name: BackendsEnum.AuthentikCoreAuthInbuiltBackend,
                label: msg("User database + standard password"),
            },
            {
                name: BackendsEnum.AuthentikCoreAuthTokenBackend,
                label: msg("User database + app passwords"),
            },
            {
                name: BackendsEnum.AuthentikSourcesLdapAuthLdapBackend,
                label: msg("User database + LDAP password"),
            },
            {
                name: BackendsEnum.AuthentikSourcesKerberosAuthKerberosBackend,
                label: msg("User database + Kerberos password"),
            },
        ];

        return html` <span>
                ${msg("Validate the user's password against the selected backend(s).")}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${this.instance?.name || ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
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
                            .options=${backends}
                            .value=${backends
                                .map(({ name }) => name)
                                .filter((name) => this.isBackendSelected(name))}
                        ></ak-checkbox-group>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Configuration flow")}
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
                            .renderDescription=${(flow: Flow): TemplateResult => {
                                return html`${flow.name}`;
                            }}
                            .value=${(flow: Flow | undefined): string | undefined => {
                                return flow?.pk;
                            }}
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
                        >
                        </ak-search-select>
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
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Failed attempts before lockout", {
                            id: "password-stage.lockout-threshold.label",
                        })}
                        required
                        name="failedAttemptsBeforeLockout"
                    >
                        <input
                            type="number"
                            min="0"
                            value="${this.instance?.failedAttemptsBeforeLockout ?? 0}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Lock password login after this many consecutive failed attempts. Set to 0 to disable lockout.",
                                {
                                    id: "password-stage.lockout-threshold.description",
                                },
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        name="showLastAttemptWarning"
                        label=${msg("Show last-attempt warning", {
                            id: "password-stage.last-attempt-warning.label",
                        })}
                        ?checked=${this.instance?.showLastAttemptWarning ?? false}
                        help=${msg(
                            "Show a warning when the user has one password attempt remaining.",
                            {
                                id: "password-stage.last-attempt-warning.description",
                            },
                        )}
                    ></ak-switch-input>
                    <ak-form-element-horizontal
                        label=${msg("Last-attempt warning message", {
                            id: "password-stage.last-attempt-warning-message.label",
                        })}
                        name="lastAttemptWarningMessage"
                    >
                        <input
                            type="text"
                            value="${this.instance?.lastAttemptWarningMessage ?? ""}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Leave blank to use the default last-attempt warning.", {
                                id: "password-stage.last-attempt-warning-message.description",
                            })}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        name="showLockoutMessage"
                        label=${msg("Show lockout message")}
                        ?checked=${this.instance?.showLockoutMessage ?? false}
                        help=${msg("Show a message to the user when their account is locked out.")}
                    ></ak-switch-input>
                    <ak-form-element-horizontal
                        label=${msg("Lockout message")}
                        name="lockoutMessage"
                    >
                        <input
                            type="text"
                            value="${this.instance?.lockoutMessage ?? ""}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Leave blank to use the default lockout message.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        name="allowShowPassword"
                        label="Allow Show Password"
                        ?checked=${this.instance?.allowShowPassword ?? false}
                        help=${msg("Provide users with a 'show password' button.")}
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
