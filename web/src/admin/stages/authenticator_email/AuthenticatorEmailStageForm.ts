import "#components/ak-secret-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import { RenderFlowOption } from "#admin/flows/utils";
import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    AuthenticatorEmailStage,
    Flow,
    FlowDesignationEnum,
    FlowsApi,
    FlowsInstancesListRequest,
    StagesApi,
    TypeCreate,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-authenticator-email-form")
export class AuthenticatorEmailStageForm extends BaseStageForm<AuthenticatorEmailStage> {
    async loadInstance(pk: string): Promise<AuthenticatorEmailStage> {
        const stage = await new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEmailRetrieve({
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

    async send(data: AuthenticatorEmailStage): Promise<AuthenticatorEmailStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEmailUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorEmailStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEmailCreate({
            authenticatorEmailStageRequest: data,
        });
    }

    renderConnectionSettings(): SlottedTemplateResult {
        if (!this.showConnectionSettings) {
            return nothing;
        }
        return html`<ak-form-group open label="${msg("Connection settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal required name="host">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "host",
                            required: true,
                        },
                        msg("SMTP Host"),
                    )}
                    <input
                        id="host"
                        type="text"
                        value="${ifDefined(this.instance?.host || "")}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal required name="port">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "port",
                            required: true,
                        },
                        msg("SMTP Port"),
                    )}
                    <input
                        id="port"
                        type="number"
                        value="${this.instance?.port ?? 25}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="username">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "username",
                        },
                        msg("SMTP Username"),
                    )}
                    <input
                        id="username"
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
                <ak-form-element-horizontal required name="timeout">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "timeout",
                            required: true,
                        },
                        msg("Timeout"),
                    )}
                    <input
                        id="timeout"
                        type="number"
                        value="${this.instance?.timeout ?? 30}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal required name="fromAddress">
                    ${AKLabel(
                        {
                            slot: "label",
                            className: "pf-c-form__group-label",
                            htmlFor: "fromAddress",
                            required: true,
                        },
                        msg("From address"),
                    )}
                    <input
                        id="fromAddress"
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
            <ak-form-element-horizontal required name="name">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "name",
                        required: true,
                    },
                    msg("Name"),
                )}
                <input
                    id="name"
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal ?required=${false} name="friendlyName">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "friendlyName",
                    },
                    msg("Authenticator type name"),
                )}
                <input
                    id="friendlyName"
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
                    <ak-form-element-horizontal required name="subject">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "subject",
                                required: true,
                            },
                            msg("Subject"),
                        )}
                        <input
                            id="subject"
                            type="text"
                            value="${this.instance?.subject ?? "authentik Sign-in code"}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Subject of the verification email.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal required name="tokenExpiry">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "tokenExpiry",
                                required: true,
                            },
                            msg("Token expiration"),
                        )}
                        <input
                            id="tokenExpiry"
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
                    <ak-form-element-horizontal name="configureFlow">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "configureFlow",
                            },
                            msg("Configuration flow"),
                        )}
                        <ak-search-select
                            id="configureFlow"
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                    designation: FlowDesignationEnum.StageConfiguration,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(
                                    args,
                                );
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
                                return this.instance?.configureFlow === flow.pk;
                            }}
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="template">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "template",
                            },
                            msg("Template"),
                        )}
                        <select
                            id="template"
                            class="pf-c-form-control"
                            ?disabled=${!this.templates || this.templates.length === 0}
                        >
                            ${this.templates && this.templates.length > 0
                                ? this.templates.map((template: TypeCreate) => {
                                      return html`<option
                                          value="${template.name}"
                                          ?selected=${this.instance?.template === template.name ||
                                          (!this.instance?.template &&
                                              template.name === "email/email_otp.html")}
                                      >
                                          ${template.description}
                                      </option>`;
                                  })
                                : html`<option value="">${msg("Loading templates...")}</option>`}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Template used for the verification email.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-email-form": AuthenticatorEmailStageForm;
    }
}
