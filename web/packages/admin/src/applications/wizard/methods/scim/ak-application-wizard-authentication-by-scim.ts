import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import "@goauthentik/admin/common/ak-core-group-search.js";
import "@goauthentik/admin/common/ak-crypto-certificate-search.js";
import "@goauthentik/admin/common/ak-flow-search/ak-tenanted-flow-search.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { first } from "@goauthentik/common/utils.js";
import "@goauthentik/components/ak-multi-select.js";
import "@goauthentik/components/ak-switch-input.js";
import "@goauthentik/components/ak-text-input.js";
import "@goauthentik/elements/forms/FormGroup.js";
import "@goauthentik/elements/forms/HorizontalFormElement.js";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { PaginatedSCIMMappingList, PropertymappingsApi, type SCIMProvider } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-scim")
export class ApplicationWizardAuthenticationBySCIM extends BaseProviderPanel {
    @state()
    propertyMappings?: PaginatedSCIMMappingList;

    constructor() {
        super();
        new PropertymappingsApi(DEFAULT_CONFIG)
            .propertymappingsScimList({
                ordering: "managed",
            })
            .then((propertyMappings: PaginatedSCIMMappingList) => {
                this.propertyMappings = propertyMappings;
            });
    }

    propertyMappingConfiguration(provider?: SCIMProvider) {
        const propertyMappings = this.propertyMappings?.results ?? [];

        const configuredMappings = (providerMappings: string[]) =>
            propertyMappings.map((pm) => pm.pk).filter((pmpk) => providerMappings.includes(pmpk));

        const managedMappings = (key: string) =>
            propertyMappings
                .filter((pm) => pm.managed === `goauthentik.io/providers/scim/${key}`)
                .map((pm) => pm.pk);

        const pmUserValues = provider?.propertyMappings
            ? configuredMappings(provider?.propertyMappings ?? [])
            : managedMappings("user");

        const pmGroupValues = provider?.propertyMappingsGroup
            ? configuredMappings(provider?.propertyMappingsGroup ?? [])
            : managedMappings("group");

        const propertyPairs = propertyMappings.map((pm) => [pm.pk, pm.name]);

        return { pmUserValues, pmGroupValues, propertyPairs };
    }

    render() {
        const provider = this.wizard.provider as SCIMProvider | undefined;
        const errors = this.wizard.errors.provider;

        const { pmUserValues, pmGroupValues, propertyPairs } =
            this.propertyMappingConfiguration(provider);

        return html`<ak-wizard-title>${msg("Configure SCIM Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                <ak-text-input
                    name="name"
                    label=${msg("Name")}
                    value=${ifDefined(provider?.name)}
                    .errorMessages=${errors?.name ?? []}
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
                            .errorMessages=${errors?.url ?? []}
                        >
                        </ak-text-input>
                        <ak-text-input
                            name="token"
                            label=${msg("Token")}
                            value="${first(provider?.token, "")}"
                            .errorMessages=${errors?.token ?? []}
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
                            <ak-core-group-search
                                .group=${provider?.filterGroup}
                            ></ak-core-group-search>
                            <p class="pf-c-form__helper-text">
                                ${msg("Only sync users within the selected group.")}
                            </p>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
                <ak-form-group ?expanded=${true}>
                    <span slot="header"> ${msg("Attribute mapping")} </span>
                    <div slot="body" class="pf-c-form">
                        <ak-multi-select
                            label=${msg("User Property Mappings")}
                            required
                            name="propertyMappings"
                            .options=${propertyPairs}
                            .values=${pmUserValues}
                            .richhelp=${html` <p class="pf-c-form__helper-text">
                                    ${msg("Property mappings used for user mapping.")}
                                </p>
                                <p class="pf-c-form__helper-text">
                                    ${msg("Hold control/command to select multiple items.")}
                                </p>`}
                        ></ak-multi-select>
                        <ak-multi-select
                            label=${msg("Group Property Mappings")}
                            required
                            name="propertyMappingsGroup"
                            .options=${propertyPairs}
                            .values=${pmGroupValues}
                            .richhelp=${html` <p class="pf-c-form__helper-text">
                                    ${msg("Property mappings used for group creation.")}
                                </p>
                                <p class="pf-c-form__helper-text">
                                    ${msg("Hold control/command to select multiple items.")}
                                </p>`}
                        ></ak-multi-select>
                    </div>
                </ak-form-group>
            </form>`;
    }
}

export default ApplicationWizardAuthenticationBySCIM;
