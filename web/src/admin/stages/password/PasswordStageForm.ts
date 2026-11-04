import "#components/ak-number-input";
import "#components/ak-text-input";
import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { WithLicenseSummary } from "#elements/mixins/license";

import { AKLabel } from "#components/ak-label";

import { AKFlowSearch } from "#admin/common/ak-flow-search/AKFlowSearch";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { BackendsEnum, FlowDesignationEnum, PasswordStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
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

    protected renderLockoutSettings(): TemplateResult {
        const readOnly = !this.hasEnterpriseLicense;

        return html`<ak-number-input
                label=${msg("Failed attempts before lockout", {
                    id: "password-stage.lockout-threshold.label",
                })}
                required
                name="failedAttemptsBeforeLockout"
                min=${0}
                value=${this.instance?.failedAttemptsBeforeLockout ?? 0}
                ?readonly=${readOnly}
                help=${
                    readOnly
                        ? msg("Password lockout requires an Enterprise license.", {
                              id: "password-stage.lockout-threshold.enterprise.description",
                          })
                        : msg(
                              "Lock password login after this many consecutive failed attempts, until an administrator unlocks it. LDAP users are exempt while any LDAP source is enabled; Kerberos users are exempt when linked to an enabled source. The corresponding backend must be selected. Set to 0 to never lock.",
                              { id: "password-stage.lockout-threshold.description" },
                          )
                }
            ></ak-number-input>
            <ak-text-input
                label=${msg("Last-attempt warning message", {
                    id: "password-stage.last-attempt-warning-message.label",
                })}
                name="lastAttemptWarningMessage"
                value=${this.instance?.lastAttemptWarningMessage ?? ""}
                ?readonly=${readOnly}
                help=${msg(
                    "Warning shown when the user has one password attempt remaining. Leave blank to show no warning.",
                    { id: "password-stage.last-attempt-warning-message.description" },
                )}
            ></ak-text-input>
            <ak-text-input
                label=${msg("Lockout message", {
                    id: "password-stage.lockout-message.label",
                })}
                name="lockoutMessage"
                value=${this.instance?.lockoutMessage ?? ""}
                ?readonly=${readOnly}
                help=${msg(
                    "Message shown when the user's password has been locked. Leave blank to show a generic authentication error.",
                    { id: "password-stage.lockout-message.description" },
                )}
            ></ak-text-input>`;
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
            <ak-text-input
                label=${msg("Stage Name", {
                    id: "stage.name.label",
                })}
                required
                name="name"
                value=${this.instance?.name || ""}
                placeholder=${msg("Type a name for this stage...", {
                    id: "stage.name.placeholder",
                })}
                ?autofocus=${!this.instance}
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
                        ${AKFlowSearch({
                            name: "configureFlow",
                            flowType: FlowDesignationEnum.StageConfiguration,
                            value: this.instance?.configureFlow,
                            blankable: true,
                            defaultFlowSlug: this.instance?.pk ? null : "default-password-change",
                        })}
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
                                "How many attempts a user has before the flow is canceled. This only cancels the flow, it does not lock the user's password.",
                                {
                                    id: "password-stage.failed-attempts-before-cancel.description",
                                },
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    ${this.renderLockoutSettings()}
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
