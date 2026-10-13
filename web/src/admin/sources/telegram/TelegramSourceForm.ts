import "#components/ak-slug-input";
import "#components/ak-text-input";
import "#components/ak-secret-search-input";
import "#elements/forms/Radio";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#components/ak-switch-input";
import { propertyMappingsProvider, propertyMappingsSelector } from "./TelegramSourceFormHelpers.js";

import { aki } from "#common/api/client";

import { ifPresent } from "#elements/utils/attributes";

import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import { BaseSourceForm } from "#admin/sources/BaseSourceForm";
import {
    AKSourceAuthenticationFlowField,
    AKSourceEnrollmentFlowField,
    AKSourcePreAuthenticationFlowField,
} from "#admin/sources/components/flow-fields";
import { UserMatchingModeToLabel } from "#admin/sources/oauth/utils";

import {
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
    protected endpoints = {
        load: (slug: string) => aki(SourcesApi).sourcesTelegramRetrieve({ slug }),
        create: (telegramSource: TelegramSource) =>
            aki(SourcesApi).sourcesTelegramCreate({
                telegramSourceRequest: telegramSource as unknown as TelegramSourceRequest,
            }),
        update: (slug: string, patchedTelegramSourceRequest: TelegramSource) =>
            aki(SourcesApi).sourcesTelegramPartialUpdate({ slug, patchedTelegramSourceRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                label=${msg("Source Name")}
                placeholder=${msg("Type a name for this source...")}
                required
                name="name"
                value="${ifDefined(this.instance?.name)}"
            ></ak-text-input>
            <ak-slug-input
                name="slug"
                placeholder=${msg("e.g. my-telegram-source")}
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
                        ?selected=${
                            this.instance?.userMatchingMode === UserMatchingModeEnum.Identifier
                        }
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailLink}
                        ?selected=${
                            this.instance?.userMatchingMode === UserMatchingModeEnum.EmailLink
                        }
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailDeny}
                        ?selected=${
                            this.instance?.userMatchingMode === UserMatchingModeEnum.EmailDeny
                        }
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailDeny)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameLink}
                        ?selected=${
                            this.instance?.userMatchingMode === UserMatchingModeEnum.UsernameLink
                        }
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameDeny}
                        ?selected=${
                            this.instance?.userMatchingMode === UserMatchingModeEnum.UsernameDeny
                        }
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
            <ak-secret-search-input
                name="botTokenRef"
                label=${msg("Bot token")}
                value=${ifPresent(this.instance?.botTokenRef)}
                required
                help=${msg("Token of the Telegram bot.", {
                    id: "source.telegram.form.secret.description",
                })}
            ></ak-secret-search-input>
            <ak-switch-input
                name="requestMessageAccess"
                label=${msg("Request access to send messages from your bot")}
                ?checked=${this.instance?.requestMessageAccess ?? true}
            ></ak-switch-input>
            <ak-form-group label="${msg("Flow settings")}">
                <div class="pf-c-form">
                    ${AKSourcePreAuthenticationFlowField({ value: this.instance?.preAuthenticationFlow, sourcePk: this.instance?.pk })}
                    ${AKSourceAuthenticationFlowField({ value: this.instance?.authenticationFlow, sourcePk: this.instance?.pk })}
                    ${AKSourceEnrollmentFlowField({ value: this.instance?.enrollmentFlow, sourcePk: this.instance?.pk })}
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
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-telegram-form": TelegramSourceForm;
    }
}
