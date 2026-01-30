import "#elements/forms/HorizontalFormElement";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#components/ak-text-input";
import "#components/ak-textarea-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AccountLockdownStage, FlowsInstancesListDesignationEnum, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-account-lockdown-form")
export class AccountLockdownStageForm extends BaseStageForm<AccountLockdownStage> {
    loadInstance(pk: string): Promise<AccountLockdownStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAccountLockdownRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: AccountLockdownStage): Promise<AccountLockdownStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAccountLockdownUpdate({
                stageUuid: this.instance.pk || "",
                accountLockdownStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesAccountLockdownCreate({
            accountLockdownStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html`
            <span>
                ${msg(
                    "This stage executes account lockdown actions on a target user. Configure which actions to perform when this stage runs.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="deactivateUser">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.instance?.deactivateUser ?? true}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Deactivate user")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg("Deactivate the user account (set is_active to False).")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="setUnusablePassword">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.instance?.setUnusablePassword ?? true}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Set unusable password")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg("Set an unusable password for the user.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="deleteSessions">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.instance?.deleteSessions ?? true}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Delete sessions")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg("Delete all active sessions for the user.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="revokeTokens">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${this.instance?.revokeTokens ?? true}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Revoke tokens")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Revoke all tokens for the user (API, app password, recovery, verification).",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Self-service completion")}">
                <span class="pf-c-form__helper-text">
                    ${msg(
                        "Configure what happens after a user locks their own account. Since all sessions are deleted, the user cannot continue in the current flow and will be redirected to a separate completion flow.",
                    )}
                </span>
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Completion flow")}
                        name="selfServiceCompletionFlow"
                    >
                        <ak-flow-search
                            placeholder=${msg("Select a completion flow...")}
                            flowType=${FlowsInstancesListDesignationEnum.StageConfiguration}
                            .currentFlow=${this.instance?.selfServiceCompletionFlow}
                        ></ak-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow to redirect users to after self-service lockdown. This flow must not require authentication since the user's session is deleted. If not set, the user will be shown the message below.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-text-input
                        label=${msg("Self-service message title")}
                        name="selfServiceMessageTitle"
                        value="${ifDefined(this.instance?.selfServiceMessageTitle)}"
                        help=${msg("Title shown to users after self-service lockdown.")}
                    >
                    </ak-text-input>
                    <ak-textarea-input
                        label=${msg("Self-service message")}
                        name="selfServiceMessage"
                        value=${ifDefined(this.instance?.selfServiceMessage)}
                        rows="6"
                        help=${msg(
                            "HTML message shown to users after self-service lockdown. Supports HTML formatting.",
                        )}
                    >
                    </ak-textarea-input>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-account-lockdown-form": AccountLockdownStageForm;
    }
}
