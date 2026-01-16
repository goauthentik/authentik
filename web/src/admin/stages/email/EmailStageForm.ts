import "#components/ak-secret-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/utils/TimeDeltaHelp";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { SlottedTemplateResult } from "#elements/types";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { EmailStage, StagesApi, TypeCreate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-email-form")
export class EmailStageForm extends BaseStageForm<EmailStage> {
    async loadInstance(pk: string): Promise<EmailStage> {
        const stage = await new StagesApi(DEFAULT_CONFIG).stagesEmailRetrieve({
            stageUuid: pk,
        });
        this.showConnectionSettings = !stage.useGlobalSettings;
        return stage;
    }

    async load(): Promise<void> {
        this.templates = await new StagesApi(DEFAULT_CONFIG).stagesEmailTemplatesList();
    }

    templates?: TypeCreate[];

    @property({ type: Boolean })
    showConnectionSettings = false;

    async send(data: EmailStage): Promise<EmailStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesEmailPartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedEmailStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesEmailCreate({
            emailStageRequest: data,
        });
    }

    renderConnectionSettings(): SlottedTemplateResult {
        if (!this.showConnectionSettings) {
            return nothing;
        }
        return html`<ak-form-group label="${msg("Connection settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal label=${msg("SMTP Host")} required name="host">
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.host || "")}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${msg("SMTP Port")} required name="port">
                    <input
                        type="number"
                        value="${this.instance?.port ?? 25}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${msg("SMTP Username")} name="username">
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.username || "")}"
                        class="pf-c-form-control"
                    />
                </ak-form-element-horizontal>
                <ak-secret-text-input
                    label=${msg("SMTP Password")}
                    name="password"
                    ?revealed=${!this.instance}
                ></ak-secret-text-input>
                <ak-switch-input
                    name="useTls"
                    label=${msg("Use TLS")}
                    ?checked=${this.instance?.useTls ?? true}
                >
                </ak-switch-input>
                <ak-switch-input
                    name="useSsl"
                    label=${msg("Use SSL")}
                    ?checked=${this.instance?.useSsl ?? false}
                >
                </ak-switch-input>
                <ak-form-element-horizontal label=${msg("Timeout")} required name="timeout">
                    <input
                        type="number"
                        value="${this.instance?.timeout ?? 30}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("From address")}
                    required
                    name="fromAddress"
                >
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.fromAddress || "system@authentik.local")}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>`;
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Verify the user's email address by sending them a one-time-link. Can also be used for recovery to verify the user's authenticity.",
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
                        name="activateUserOnSuccess"
                        ?checked=${this.instance?.activateUserOnSuccess ?? true}
                        label=${msg("Activate pending user on success")}
                        help=${msg(
                            "When a user returns from the email successfully, their account will be activated.",
                        )}
                    ></ak-switch-input>
                    <ak-switch-input
                        name="useGlobalSettings"
                        ?checked=${this.instance?.useGlobalSettings ?? true}
                        @change=${(ev: Event) => {
                            const target = ev.target as HTMLInputElement;
                            this.showConnectionSettings = !target.checked;
                        }}
                        label=${msg("Use global connection settings")}
                        help=${msg(
                            "When enabled, global email connection settings will be used and connection settings below will be ignored.",
                        )}
                    ></ak-switch-input>
                    <ak-form-element-horizontal
                        label=${msg("Token expiration")}
                        required
                        name="tokenExpiry"
                    >
                        <input
                            type="text"
                            value="${this.instance?.tokenExpiry ?? "minutes=30"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Time the token sent is valid.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Subject")} required name="subject">
                        <input
                            type="text"
                            value="${this.instance?.subject ?? "authentik"}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Template")} required name="template">
                        <select name="users" class="pf-c-form-control">
                            ${this.templates?.map((template) => {
                                const selected = this.instance?.template === template.name;
                                return html`<option
                                    value=${ifDefined(template.name)}
                                    ?selected=${selected}
                                >
                                    ${template.description}
                                </option>`;
                            })}
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Account Recovery Max Attempts")}
                        required
                        name="recoveryMaxAttempts"
                    >
                        <input
                            type="number"
                            value="${this.instance?.recoveryMaxAttempts ?? 5}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Account Recovery Cache Timeout")}
                        required
                        name="recoveryCacheTimeout"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.recoveryCacheTimeout || "minutes=5")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "The time window used to count recent account recovery attempts.",
                            )}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            ${this.renderConnectionSettings()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-email-form": EmailStageForm;
    }
}
