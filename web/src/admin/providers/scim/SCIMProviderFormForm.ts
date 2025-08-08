import "#components/ak-hidden-text-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { propertyMappingsProvider, propertyMappingsSelector } from "./SCIMProviderFormHelpers.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import {
    CompatibilityModeEnum,
    CoreApi,
    CoreGroupsListRequest,
    Group,
    SCIMProvider,
    ValidationError,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export function renderForm(provider?: Partial<SCIMProvider>, errors: ValidationError = {}) {
    return html`
        <ak-text-input
            name="name"
            value=${ifDefined(provider?.name)}
            label=${msg("Name")}
            .errorMessages=${errors?.name}
            required
            help=${msg("Method's display Name.")}
        ></ak-text-input>
        <ak-form-group open label="${msg("Protocol settings")}">
            <div class="pf-c-form">
                <ak-text-input
                    name="url"
                    label=${msg("URL")}
                    value="${provider?.url ?? ""}"
                    .errorMessages=${errors?.url}
                    required
                    help=${msg("SCIM base url, usually ends in /v2.")}
                    input-hint="code"
                ></ak-text-input>

                <ak-switch-input
                    name="verifyCertificates"
                    label=${msg("Verify SCIM server's certificates")}
                    ?checked=${provider?.verifyCertificates ?? true}
                >
                </ak-switch-input>

                <ak-hidden-text-input
                    name="token"
                    label=${msg("Token")}
                    value="${provider?.token ?? ""}"
                    .errorMessages=${errors?.token}
                    required
                    help=${msg(
                        "Token to authenticate with. Currently only bearer authentication is supported.",
                    )}
                    input-hint="code"
                ></ak-hidden-text-input>
                <ak-radio-input
                    name="compatibilityMode"
                    label=${msg("Compatibility Mode")}
                    .value=${provider?.compatibilityMode}
                    required
                    .options=${[
                        {
                            label: msg("Default"),
                            value: CompatibilityModeEnum.Default,
                            default: true,
                            description: html`${msg("Default behavior.")}`,
                        },
                        {
                            label: msg("AWS"),
                            value: CompatibilityModeEnum.Aws,
                            description: html`${msg(
                                "Altered behavior for usage with Amazon Web Services.",
                            )}`,
                        },
                        {
                            label: msg("Slack"),
                            value: CompatibilityModeEnum.Slack,
                            description: html`${msg("Altered behavior for usage with Slack.")}`,
                        },
                    ]}
                    help=${msg(
                        "Alter authentik's behavior for vendor-specific SCIM implementations.",
                    )}
                ></ak-radio-input>
                <ak-form-element-horizontal name="dryRun">
                    <label class="pf-c-switch">
                        <input
                            class="pf-c-switch__input"
                            type="checkbox"
                            ?checked=${provider?.dryRun ?? false}
                        />
                        <span class="pf-c-switch__toggle">
                            <span class="pf-c-switch__toggle-icon">
                                <i class="fas fa-check" aria-hidden="true"></i>
                            </span>
                        </span>
                        <span class="pf-c-switch__label">${msg("Enable dry-run mode")}</span>
                    </label>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "When enabled, mutating requests will be dropped and logged instead.",
                        )}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>
        <ak-form-group open label="${msg("User filtering")}">
            <div class="pf-c-form">
                <ak-switch-input
                    name="excludeUsersServiceAccount"
                    label=${msg("Exclude service accounts")}
                    ?checked=${provider?.excludeUsersServiceAccount ?? true}
                >
                </ak-switch-input>

                <ak-form-element-horizontal label=${msg("Group")} name="filterGroup">
                    <ak-search-select
                        .fetchObjects=${async (query?: string): Promise<Group[]> => {
                            const args: CoreGroupsListRequest = {
                                ordering: "name",
                                includeUsers: false,
                            };
                            if (query !== undefined) {
                                args.search = query;
                            }
                            const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(args);
                            return groups.results;
                        }}
                        .renderElement=${(group: Group): string => {
                            return group.name;
                        }}
                        .value=${(group: Group | undefined): string | undefined => {
                            return group ? group.pk : undefined;
                        }}
                        .selected=${(group: Group): boolean => {
                            return group.pk === provider?.filterGroup;
                        }}
                        blankable
                    >
                    </ak-search-select>
                    <p class="pf-c-form__helper-text">
                        ${msg("Only sync users within the selected group.")}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>

        <ak-form-group open label="${msg("Attribute mapping")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("User Property Mappings")}
                    name="propertyMappings"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${propertyMappingsProvider}
                        .selector=${propertyMappingsSelector(
                            provider?.propertyMappings,
                            "goauthentik.io/providers/scim/user",
                        )}
                        available-label=${msg("Available User Property Mappings")}
                        selected-label=${msg("Selected User Property Mappings")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg("Property mappings used to user mapping.")}
                    </p>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Group Property Mappings")}
                    name="propertyMappingsGroup"
                >
                    <ak-dual-select-dynamic-selected
                        .provider=${propertyMappingsProvider}
                        .selector=${propertyMappingsSelector(
                            provider?.propertyMappingsGroup,
                            "goauthentik.io/providers/scim/group",
                        )}
                        available-label=${msg("Available Group Property Mappings")}
                        selected-label=${msg("Selected Group Property Mappings")}
                    ></ak-dual-select-dynamic-selected>
                    <p class="pf-c-form__helper-text">
                        ${msg("Property mappings used to group creation.")}
                    </p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>
    `;
}
