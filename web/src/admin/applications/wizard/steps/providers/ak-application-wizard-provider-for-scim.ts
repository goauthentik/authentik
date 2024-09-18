import "@goauthentik/admin/common/ak-core-group-search";
import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-branded-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-multi-select";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { PaginatedSCIMMappingList, PropertymappingsApi, type SCIMProvider } from "@goauthentik/api";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm";

@customElement("ak-application-wizard-provider-for-scim")
export class ApplicationWizardSCIMProvider extends ApplicationWizardProviderForm<SCIMProvider> {
    @state()
    propertyMappings?: PaginatedSCIMMappingList;

    label = msg("Configure SCIM");

    constructor() {
        super();
        new PropertymappingsApi(DEFAULT_CONFIG)
            .propertymappingsProviderScimList({
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

    renderForm(provider: SCIMProvider) {
        const { pmUserValues, pmGroupValues, propertyPairs } =
            this.propertyMappingConfiguration(provider);

        return html` <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
            <ak-text-input
                name="name"
                label=${msg("Name")}
                value=${ifDefined(provider?.name)}
                .errorMessages=${this.errorMessages("name")}
                required
            ></ak-text-input>
            <ak-form-group expanded>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="url"
                        label=${msg("URL")}
                        value="${provider?.url ?? ""}"
                        required
                        help=${msg("SCIM base url, usually ends in /v2.")}
                        .errorMessages=${this.errorMessages("url")}
                    >
                    </ak-text-input>
                    <ak-text-input
                        name="token"
                        label=${msg("Token")}
                        value="${provider?.token ?? ""}"
                        .errorMessages=${this.errorMessages("token")}
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
                        ?checked=${provider?.excludeUsersServiceAccount ?? true}
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
                        name="propertyMappings"
                        .options=${propertyPairs}
                        .values=${pmUserValues}
                        .richhelp=${html`
                            <p class="pf-c-form__helper-text">
                                ${msg("Property mappings used for user mapping.")}
                            </p>
                        `}
                    ></ak-multi-select>
                    <ak-multi-select
                        label=${msg("Group Property Mappings")}
                        name="propertyMappingsGroup"
                        .options=${propertyPairs}
                        .values=${pmGroupValues}
                        .richhelp=${html`
                            <p class="pf-c-form__helper-text">
                                ${msg("Property mappings used for group creation.")}
                            </p>
                        `}
                    ></ak-multi-select>
                </div>
            </ak-form-group>
        </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("SCIM Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider as SCIMProvider);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-scim": ApplicationWizardSCIMProvider;
    }
}
