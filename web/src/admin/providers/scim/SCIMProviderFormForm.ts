import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { first } from "@goauthentik/common/utils.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CoreApi,
    CoreGroupsListRequest,
    Group,
    SCIMProvider,
    ValidationError,
} from "@goauthentik/api";

import { propertyMappingsProvider, propertyMappingsSelector } from "./SCIMProviderFormHelpers.js";

export function renderForm(provider?: Partial<SCIMProvider>, errors: ValidationError = {}) {
    return html`
        <ak-text-input
            name="name"
            value=${ifDefined(provider?.name)}
            label=${msg("Name")}
            .errorMessages=${errors?.name ?? []}
            required
            help=${msg("Method's display Name.")}
        ></ak-text-input>
        <ak-form-group expanded>
            <span slot="header"> ${msg("Protocol settings")} </span>
            <div slot="body" class="pf-c-form">
                <ak-text-input
                    name="url"
                    label=${msg("URL")}
                    value="${first(provider?.url, "")}"
                    .errorMessages=${errors?.url ?? []}
                    required
                    help=${msg("SCIM base url, usually ends in /v2.")}
                    inputHint="code"
                ></ak-text-input>

                <ak-switch-input
                    name="verifyCertificates"
                    label=${msg("Verify SCIM server's certificates")}
                    ?checked=${provider?.verifyCertificates ?? true}
                >
                </ak-switch-input>

                <ak-text-input
                    name="token"
                    label=${msg("Token")}
                    value="${provider?.token ?? ""}"
                    .errorMessages=${errors?.token ?? []}
                    required
                    help=${msg(
                        "Token to authenticate with. Currently only bearer authentication is supported.",
                    )}
                    inputHint="code"
                ></ak-text-input>
            </div>
        </ak-form-group>
        <ak-form-group expanded>
            <span slot="header">${msg("User filtering")}</span>
            <div slot="body" class="pf-c-form">
                <ak-switch-input
                    name="excludeUsersServiceAccount"
                    label=${msg("Exclude service accounts")}
                    ?checked=${first(provider?.excludeUsersServiceAccount, true)}
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

        <ak-form-group expanded>
            <span slot="header"> ${msg("Attribute mapping")} </span>
            <div slot="body" class="pf-c-form">
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
