import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-tenanted-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CoreApi,
    CoreGroupsListRequest,
    type Group,
    PaginatedSCIMMappingList,
    PropertymappingsApi,
    type SCIMProvider,
} from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-scim")
export class ApplicationWizardAuthenticationBySCIM extends BaseProviderPanel {
    @state()
    propertyMappings?: PaginatedSCIMMappingList;

    constructor() {
        super();
        new PropertymappingsApi(DEFAULT_CONFIG)
            .propertymappingsScopeList({
                ordering: "scope_name",
            })
            .then((propertyMappings: PaginatedSCIMMappingList) => {
                this.propertyMappings = propertyMappings;
            });
    }

    render() {
        const provider = this.wizard.provider as SCIMProvider | undefined;

        return html`<form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input
                name="name"
                label=${msg("Name")}
                value=${ifDefined(provider?.name)}
                required
            ></ak-text-input>
            <ak-form-group expanded>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="url"
                        label=${msg("URL")}
                        value="${first(provider?.url, "")}"
                        required
                        help=${msg("SCIM base url, usually ends in /v2.")}
                    >
                    </ak-text-input>
                    <ak-text-input
                        name="token"
                        label=${msg("Token")}
                        value="${first(provider?.token, "")}"
                        required
                        help=${msg(
                            "Token to authenticate with. Currently only bearer authentication is supported.",
                        )}
                    >
                    </ak-text-input>
                </div>
            </ak-form-group>
            <ak-form-group expanded>
                <span slot="header">${msg("User filtering")}</span>
                <div slot="body" class="pf-c-form">
                    <ak-switch-input
                        name="excludeUsersServiceAccount"
                        ?checked=${first(provider?.excludeUsersServiceAccount, true)}
                        label=${msg("Exclude service accounts")}
                    ></ak-switch-input>
                    <ak-form-element-horizontal label=${msg("Group")} name="filterGroup">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Group[]> => {
                                const args: CoreGroupsListRequest = {
                                    ordering: "name",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(
                                    args,
                                );
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
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Only sync users within the selected group.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group ?expanded=${true}>
                <span slot="header"> ${msg("Attribute mapping")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User Property Mappings")}
                        ?required=${true}
                        name="propertyMappings"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results.map((mapping) => {
                                let selected = false;
                                if (!provider?.propertyMappings) {
                                    selected =
                                        mapping.managed === "goauthentik.io/providers/scim/user" ||
                                        false;
                                } else {
                                    selected = Array.from(provider?.propertyMappings).some((su) => {
                                        return su == mapping.pk;
                                    });
                                }
                                return html`<option
                                    value=${ifDefined(mapping.pk)}
                                    ?selected=${selected}
                                >
                                    ${mapping.name}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings used to user mapping.")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group Property Mappings")}
                        ?required=${true}
                        name="propertyMappingsGroup"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.propertyMappings?.results.map((mapping) => {
                                let selected = false;
                                if (!provider?.propertyMappingsGroup) {
                                    selected =
                                        mapping.managed === "goauthentik.io/providers/scim/group";
                                } else {
                                    selected = Array.from(provider?.propertyMappingsGroup).some(
                                        (su) => {
                                            return su == mapping.pk;
                                        },
                                    );
                                }
                                return html`<option
                                    value=${ifDefined(mapping.pk)}
                                    ?selected=${selected}
                                >
                                    ${mapping.name}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings used to group creation.")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}

export default ApplicationWizardAuthenticationBySCIM;
