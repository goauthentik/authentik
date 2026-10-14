import "#components/ak-secret-text-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#components/ak-switch-input";
import { aki } from "#common/api/client";

import { SlottedTemplateResult } from "#elements/types";

import { AKFlowSearch } from "#admin/common/ak-flow-search/AKFlowSearch";
import { AKEmailTemplateField } from "#admin/common/AKEmailTemplateSearch";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { AuthenticatorEmailStage, FlowDesignationEnum, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-authenticator-email-form")
export class AuthenticatorEmailStageForm extends BaseStageForm<AuthenticatorEmailStage> {
    async loadInstance(pk: string): Promise<AuthenticatorEmailStage> {
        const stage = await aki(StagesApi).stagesAuthenticatorEmailRetrieve({
            stageUuid: pk,
        });

        this.showConnectionSettings = !stage.useGlobalSettings;

        return stage;
    }

    @property({ type: Boolean })
    showConnectionSettings = false;

    async send(data: AuthenticatorEmailStage): Promise<AuthenticatorEmailStage> {
        if (this.instance) {
            return aki(StagesApi).stagesAuthenticatorEmailUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorEmailStageRequest: data,
            });
        }

        return aki(StagesApi).stagesAuthenticatorEmailCreate({
            authenticatorEmailStageRequest: data,
        });
    }

    renderConnectionSettings(): SlottedTemplateResult {
        if (!this.showConnectionSettings) {
            return nothing;
        }

        return html`<ak-form-group open label="${msg("Connection settings")}">
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
                    name="password"
                    label=${msg("SMTP Password")}
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
                    <p class="pf-c-form__helper-text">
                        ${msg("Email address the verification email will be sent from.")}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>`;
    }

    protected override renderForm(): TemplateResult {
        return html` <span> ${msg("Stage used to configure an email-based authenticator.")}</span>
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
            <ak-form-element-horizontal
                label=${msg("Authenticator type name")}
                ?required=${false}
                name="friendlyName"
            >
                <input
                    type="text"
                    value="${this.instance?.friendlyName ?? ""}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Display name of this authenticator, used by users when they enroll an authenticator.",
                    )}
                </p>
            </ak-form-element-horizontal>
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
            ${this.renderConnectionSettings()}
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Subject")} required name="subject">
                        <input
                            type="text"
                            value="${this.instance?.subject ?? "authentik Sign-in code"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Subject of the verification email.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Token expiration")}
                        required
                        name="tokenExpiry"
                    >
                        <input
                            type="text"
                            value="${this.instance?.tokenExpiry ?? "minutes=15"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Time the token sent is valid (Format: hours=3,minutes=17,seconds=300).",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Configuration flow")}
                        name="configureFlow"
                    >
                        ${AKFlowSearch({
                            name: "configureFlow",
                            flowType: FlowDesignationEnum.StageConfiguration,
                            value: this.instance?.configureFlow,
                            blankable: true,
                        })}
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    ${AKEmailTemplateField({
                        name: "template",
                        required: true,
                        value: this.instance?.template,
                        defaultTemplate: "goauthentik.io/email/email-otp",
                        help: msg("Template used for the verification email."),
                    })}
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-email-form": AuthenticatorEmailStageForm;
    }
}
