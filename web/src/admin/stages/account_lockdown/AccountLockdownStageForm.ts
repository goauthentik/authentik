import "#elements/forms/HorizontalFormElement";

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
                            ${msg("Revoke all API and app password tokens for the user.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Self-service completion message")}">
                <span class="pf-c-form__helper-text">
                    ${msg(
                        "This message is shown to users after they lock their own account (self-service lockdown).",
                    )}
                </span>
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Title")}
                        name="selfServiceMessageTitle"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.selfServiceMessageTitle || "Your account has been locked")}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Message")}
                        name="selfServiceMessage"
                    >
                        <textarea class="pf-c-form-control" rows="5">${this.instance?.selfServiceMessage || "<p>You have been logged out of all sessions and your password has been invalidated.</p><p>To regain access to your account, please contact your IT administrator or security team.</p>"}</textarea>
                        <p class="pf-c-form__helper-text">
                            ${msg("HTML is supported. This message is displayed after the user's sessions are terminated.")}
                        </p>
                    </ak-form-element-horizontal>
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
