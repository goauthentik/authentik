import "#admin/common/ak-flow-search/ak-source-flow-search";
import "#components/ak-slug-input";
import "#components/ak-text-input";
import "#components/ak-secret-text-input";
import "#elements/forms/Radio";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#components/ak-switch-input";

import { propertyMappingsProvider, propertyMappingsSelector } from "./BskySourceFormHelpers.js";

import { aki } from "#common/api/client";

import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import { BaseSourceForm } from "#admin/sources/BaseSourceForm";
import { GroupMatchingModeToLabel, UserMatchingModeToLabel } from "#admin/sources/oauth/utils";

import {
    BskySource,
    BskySourceRequest,
    FlowDesignationEnum,
    GroupMatchingModeEnum,
    SourcesApi,
    UserMatchingModeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-source-bsky-form")
export class BskySourceForm extends BaseSourceForm<BskySource> {
    protected endpoints = {
        load: (slug: string) => aki(SourcesApi).sourcesBskyRetrieve({ slug }),
        create: (bskySource: BskySource) =>
            aki(SourcesApi).sourcesBskyCreate({
                bskySourceRequest: bskySource as unknown as BskySourceRequest,
            }),
        update: (slug: string, patchedBskySourceRequest: BskySource) =>
            aki(SourcesApi).sourcesBskyPartialUpdate({ slug, patchedBskySourceRequest }),
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
                placeholder=${msg("e.g. my-bsky-source")}
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
            <ak-form-element-horizontal label=${msg("Scope")} name="scope">
                <input
                    type="text"
                    value="${this.instance?.scope ?? "atproto transition:generic"}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Space-separated OAuth scopes requested from the user's PDS.")}
                </p>
            </ak-form-element-horizontal>
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
            <ak-form-element-horizontal
                label=${msg("Group matching mode")}
                required
                name="groupMatchingMode"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${GroupMatchingModeEnum.Identifier}
                        ?selected=${this.instance?.groupMatchingMode ===
                        GroupMatchingModeEnum.Identifier}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                    </option>
                    <option
                        value=${GroupMatchingModeEnum.NameLink}
                        ?selected=${this.instance?.groupMatchingMode ===
                        GroupMatchingModeEnum.NameLink}
                    >
                        ${GroupMatchingModeToLabel(GroupMatchingModeEnum.NameLink)}
                    </option>
                    <option
                        value=${GroupMatchingModeEnum.NameDeny}
                        ?selected=${this.instance?.groupMatchingMode ===
                        GroupMatchingModeEnum.NameDeny}
                    >
                        ${GroupMatchingModeToLabel(GroupMatchingModeEnum.NameDeny)}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-group label="${msg("Flow settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Authentication Flow")}
                        name="authenticationFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowDesignationEnum.Authentication}
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
                            flowType=${FlowDesignationEnum.Enrollment}
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
            <ak-form-group open label="${msg("Bluesky Attribute mapping")}">
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
        "ak-source-bsky-form": BskySourceForm;
    }
}
