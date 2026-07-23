import "#elements/forms/HorizontalFormElement";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#components/ak-switch-input";
import "#components/ak-text-input";

import { aki } from "#common/api/client";
import { docLink } from "#common/global";

import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AccountLockdownStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-account-lockdown-form")
export class AccountLockdownStageForm extends BaseStageForm<AccountLockdownStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesAccountLockdownRetrieve({ stageUuid }),
        create: (accountLockdownStageRequest: AccountLockdownStage) =>
            aki(StagesApi).stagesAccountLockdownCreate({ accountLockdownStageRequest }),
        update: (stageUuid: string, accountLockdownStageRequest: AccountLockdownStage) =>
            aki(StagesApi).stagesAccountLockdownUpdate({ stageUuid, accountLockdownStageRequest }),
    };

    protected override renderForm(): SlottedTemplateResult {
        return html`<span>
                ${msg(
                    "This stage executes account lockdown actions on a target user. Configure which actions to perform when this stage runs.",
                )}
            </span>
            <a
                href=${docLink("/users-sources/user/access-control/")}
                target="_blank"
                rel="noopener noreferrer"
            >
                ${msg("Compare user access controls.", {
                    id: "account-lockdown-stage.access-control-documentation.link",
                })}
            </a>
            <ak-text-input
                label=${msg("Stage Name")}
                placeholder=${msg("Type a name for this stage...")}
                required
                name="name"
                value=${ifPresent(this.instance?.name || "")}
                ?autofocus=${!this.instance}
            ></ak-text-input>
            <ak-form-group open label=${msg("Stage-specific settings")}>
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
            <ak-form-group
                label=${msg("Self-service completion")}
                open
                description=${msg(
                    "Configure what happens after a user locks their own account. Since all sessions are deleted, the user cannot continue in the current flow and will be redirected to a separate completion flow.",
                )}
            >
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
                                "Flow to redirect users to after self-service lockdown. This flow must not require authentication since the user's session is deleted.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-account-lockdown-form": AccountLockdownStageForm;
    }
}
