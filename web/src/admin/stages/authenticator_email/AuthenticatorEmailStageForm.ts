import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    AuthenticatorEmailStage,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-email-form")
export class AuthenticatorEmailStageForm extends BaseStageForm<AuthenticatorEmailStage> {
    async loadInstance(pk: string): Promise<AuthenticatorEmailStage> {
        const stage = await new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEmailRetrieve({
            stageUuid: pk,
        });
        this.showConnectionSettings = !stage.useGlobalSettings;
        return stage;
    }

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

    renderConnectionSettings(): TemplateResult {
        if (!this.showConnectionSettings) {
            return html``;
        }
        return html`<ak-form-group .expanded=${true}>
            <span slot="header"> ${msg("Connection settings")} </span>
            <div slot="body" class="pf-c-form">
                <ak-form-element-horizontal label=${msg("SMTP Host")} ?required=${true} name="host">
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.host || "")}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${msg("SMTP Port")} ?required=${true} name="port">
                    <input
                        type="number"
                        value="${first(this.instance?.port, 25)}"
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
                <ak-form-element-horizontal
                    label=${msg("SMTP Password")}
                    ?writeOnly=${this.instance !== undefined}
                    name="password"
                >
                    <input type="text" value="" class="pf-c-form-control" />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="useTls">
                    <label class="pf-c-switch">
                        <input
                            class="pf-c-switch__input"
                            type="checkbox"
                            ?checked=${first(this.instance?.useTls, true)}
                        />
                        <span class="pf-c-switch__toggle">
                            <span class="pf-c-switch__toggle-icon">
                                <i class="fas fa-check" aria-hidden="true"></i>
                            </span>
                        </span>
                        <span class="pf-c-switch__label">${msg("Use TLS")}</span>
                    </label>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="useSsl">
                    <label class="pf-c-switch">
                        <input
                            class="pf-c-switch__input"
                            type="checkbox"
                            ?checked=${first(this.instance?.useSsl, false)}
                        />
                        <span class="pf-c-switch__toggle">
                            <span class="pf-c-switch__toggle-icon">
                                <i class="fas fa-check" aria-hidden="true"></i>
                            </span>
                        </span>
                        <span class="pf-c-switch__label">${msg("Use SSL")}</span>
                    </label>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Timeout")}
                    ?required=${true}
                    name="timeout"
                >
                    <input
                        type="number"
                        value="${first(this.instance?.timeout, 30)}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("From address")}
                    ?required=${true}
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

    renderForm(): TemplateResult {
        return html` <span> ${msg("Stage used to configure an email-based authenticator.")} </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${first(this.instance?.name, "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Authenticator type name")}
                ?required=${false}
                name="friendlyName"
            >
                <input
                    type="text"
                    value="${first(this.instance?.friendlyName, "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Display name of this authenticator, used by users when they enroll an authenticator.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="useGlobalSettings">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.useGlobalSettings, true)}
                        @change=${(ev: Event) => {
                            const target = ev.target as HTMLInputElement;
                            this.showConnectionSettings = !target.checked;
                        }}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Use global connection settings")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When enabled, global email connection settings will be used and connection settings below will be ignored.",
                    )}
                </p>
            </ak-form-element-horizontal>
            ${this.renderConnectionSettings()}
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Subject")}
                        ?required=${true}
                        name="subject"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.subject, "authentik Sign-in code")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Subject of the verification email.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Token expiration")}
                        ?required=${true}
                        name="tokenExpiry"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.tokenExpiry, "minutes=15")}"
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
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                    designation:
                                        FlowsInstancesListDesignationEnum.StageConfiguration,
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
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.",
                            )}
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
