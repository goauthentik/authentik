import "#elements/forms/HorizontalFormElement";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#components/ak-textarea-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AccountLockdownStage, StagesApi } from "@goauthentik/api";

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
                    <ak-switch-input
                        name="deactivateUser"
                        label=${msg("Deactivate user")}
                        ?checked=${this.instance?.deactivateUser ?? true}
                        help=${msg("Deactivate the user account (set is_active to False).")}
                    >
                    </ak-switch-input>
                    <ak-switch-input
                        name="setUnusablePassword"
                        label=${msg("Set unusable password")}
                        ?checked=${this.instance?.setUnusablePassword ?? true}
                        help=${msg("Set an unusable password for the user.")}
                    >
                    </ak-switch-input>
                    <ak-switch-input
                        name="deleteSessions"
                        label=${msg("Delete sessions")}
                        ?checked=${this.instance?.deleteSessions ?? true}
                        help=${msg("Delete all active sessions for the user.")}
                    >
                    </ak-switch-input>
                    <ak-switch-input
                        name="revokeTokens"
                        label=${msg("Revoke tokens")}
                        ?checked=${this.instance?.revokeTokens ?? true}
                        help=${msg(
                            "Revoke all tokens for the user (API, app password, recovery, verification).",
                        )}
                    >
                    </ak-switch-input>
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
                        required
                        value="${ifDefined(this.instance?.selfServiceMessageTitle)}"
                        help=${msg("Title shown to users after self-service lockdown.")}
                    >
                    </ak-text-input>
                    <ak-textarea-input
                        label=${msg("Self-service message")}
                        name="selfServiceMessage"
                        required
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
