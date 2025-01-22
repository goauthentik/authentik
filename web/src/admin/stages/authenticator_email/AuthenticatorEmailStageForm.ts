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
import { customElement } from "lit/decorators.js";

import {
    AuthenticatorEmailStage,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest, // NotificationWebhookMapping,
    // PropertymappingsApi,
    // PropertymappingsNotificationListRequest,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-email-form")
export class AuthenticatorEmailStageForm extends BaseStageForm<AuthenticatorEmailStage> {
    loadInstance(pk: string): Promise<AuthenticatorEmailStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEmailRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: AuthenticatorEmailStage): Promise<AuthenticatorEmailStage> {
        console.debug("HEY! send data", data);
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEmailUpdate({
                stageUuid: this.instance.pk || "",
                authenticatorEmailStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorEmailCreate({
                authenticatorEmailStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        console.debug("HEY!");
        return html` <span> ${msg("Stage used to configure an Email-based authenticator.")} </span>
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
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("From address")}
                        ?required=${true}
                        name="fromAddress"
                    >
                        <input
                            type="email"
                            value="${first(this.instance?.fromAddress, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Email address the verification email will be sent from.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Subject")}
                        ?required=${true}
                        name="subject"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.subject, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Subject of the verification email.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Template")}
                        ?required=${true}
                        name="template"
                    >
                        <textarea
                            class="pf-c-form-control"
                            required
                        >${first(this.instance?.template, "")}</textarea>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Template of the verification email. Supports HTML and Django-template syntax.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <!--
                    <ak-form-element-horizontal name="verifyOnly">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                        </label>
                        <p class="pf-c-form__helper-text">

                        </p>
                    </ak-form-element-horizontal>
                    -->
                    <ak-form-element-horizontal label=${msg("Token expiration time(in minutes)")} ?required=${true} name="token_expiry">
                    <input
                        type="number"
                        value="${first(this.instance?.tokenExpiry, 10)}"
                        class="pf-c-form-control"
                        required
                    />
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
