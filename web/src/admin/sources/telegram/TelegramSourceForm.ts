import "#admin/common/ak-flow-search/ak-source-flow-search";
import "#components/ak-slug-input";
import "#components/ak-secret-text-input";
import "#elements/forms/Radio";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#components/ak-switch-input";

import { propertyMappingsProvider, propertyMappingsSelector } from "./TelegramSourceFormHelpers.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import { BaseSourceForm } from "#admin/sources/BaseSourceForm";
import { UserMatchingModeToLabel } from "#admin/sources/oauth/utils";

import {
    FlowsInstancesListDesignationEnum,
    SourcesApi,
    TelegramSource,
    TelegramSourceRequest,
    UserMatchingModeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-source-telegram-form")
export class TelegramSourceForm extends BaseSourceForm<TelegramSource> {
    async loadInstance(pk: string): Promise<TelegramSource> {
        const source = await new SourcesApi(DEFAULT_CONFIG).sourcesTelegramRetrieve({
            slug: pk,
        });
        return source;
    }

    async send(data: TelegramSource): Promise<TelegramSource> {
        let source: TelegramSource;
        if (this.instance?.pk) {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesTelegramPartialUpdate({
                slug: this.instance.slug,
                patchedTelegramSourceRequest: data,
            });
        } else {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesTelegramCreate({
                telegramSourceRequest: data as unknown as TelegramSourceRequest,
            });
        }
        return source;
    }

    renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>

            <ak-slug-input
                name="slug"
                value=${ifDefined(this.instance?.slug)}
                label=${msg("Slug")}
                required
                input-hint="code"
            ></ak-slug-input>

            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
            ></ak-switch-input>
            <ak-switch-input
                name="promoted"
                label=${msg("Promoted")}
                ?checked=${this.instance?.promoted ?? false}
                help=${msg(
                    "When enabled, this source will be displayed as a prominent button on the login page, instead of a small icon.",
                )}
            ></ak-switch-input>
            <ak-form-element-horizontal
                label=${msg("User matching mode")}
                required
                name="userMatchingMode"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${UserMatchingModeEnum.Identifier}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.Identifier}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailDeny)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameDeny)}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Bot username")} required name="botUsername">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.botUsername)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-secret-text-input
                label=${msg("Bot token")}
                name="botToken"
                input-hint="code"
                ?required=${this.instance === undefined}
                ?revealed=${this.instance === undefined}
            ></ak-secret-text-input>
            <ak-switch-input
                name="requestMessageAccess"
                label=${msg("Request access to send messages from your bot")}
                ?checked=${this.instance?.requestMessageAccess ?? true}
            ></ak-switch-input>
            <ak-form-group label="${msg("Flow settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Pre-authentication flow")}
                        required
                        name="preAuthenticationFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.StageConfiguration}
                            .currentFlow=${this.instance?.preAuthenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-pre-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow used before authentication.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Authentication flow")}
                        name="authenticationFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.authenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when authenticating existing users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enrollment flow")}
                        name="enrollmentFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Enrollment}
                            .currentFlow=${this.instance?.enrollmentFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-enrollment"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when enrolling new users.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group open label="${msg("Telegram Attribute mapping")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User Property Mappings")}
                        name="userPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.userPropertyMappings,
                            )}
                            available-label="${msg("Available User Property Mappings")}"
                            selected-label="${msg("Selected User Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for user creation.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group Property Mappings")}
                        name="groupPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.groupPropertyMappings,
                            )}
                            available-label="${msg("Available Group Property Mappings")}"
                            selected-label="${msg("Selected Group Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for group creation.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Advanced settings")} ">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Policy engine mode")}
                        required
                        name="policyEngineMode"
                    >
                        <ak-radio
                            .options=${policyEngineModes}
                            .value=${this.instance?.policyEngineMode}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-telegram-form": TelegramSourceForm;
    }
}
