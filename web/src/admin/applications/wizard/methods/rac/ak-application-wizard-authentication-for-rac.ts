import "@goauthentik/admin/applications/wizard/ak-wizard-title";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    FlowsInstancesListDesignationEnum,
    PaginatedEndpointList,
    PaginatedRACPropertyMappingList,
    PropertymappingsApi,
    RACProvider,
    RacApi,
} from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-for-rac")
export class ApplicationWizardAuthenticationByRAC extends BaseProviderPanel {
    @state()
    endpoints?: PaginatedEndpointList;

    @state()
    propertyMappings?: PaginatedRACPropertyMappingList;

    constructor() {
        super();
        new RacApi(DEFAULT_CONFIG).racEndpointsList({}).then((endpoints) => {
            this.endpoints = endpoints;
        });
        new PropertymappingsApi(DEFAULT_CONFIG)
            .propertymappingsRacList({
                ordering: "name",
            })
            .then((propertyMappings) => {
                this.propertyMappings = propertyMappings;
            });
    }

    render() {
        const provider = this.wizard.provider as RACProvider | undefined;
        const selected = new Set(Array.from(provider?.propertyMappings ?? []));
        const errors = this.wizard.errors.provider;

        return html`<ak-wizard-title
                >${msg("Configure Remote Access Provider Provider")}</ak-wizard-title
            >
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                <ak-text-input
                    name="name"
                    label=${msg("Name")}
                    value=${ifDefined(provider?.name)}
                    .errorMessages=${errors?.name ?? []}
                    required
                ></ak-text-input>

                <ak-form-element-horizontal
                    name="authorizationFlow"
                    label=${msg("Authorization flow")}
                    ?required=${true}
                >
                    <ak-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Authorization}
                        .currentFlow=${provider?.authorizationFlow}
                        required
                    ></ak-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used when authorizing this provider.")}
                    </p>
                </ak-form-element-horizontal>

                <ak-text-input
                    name="connectionExpiry"
                    label=${msg("Connection expiry")}
                    required
                    value="${provider?.connectionExpiry ?? "hours=8"}"
                    help=${msg(
                        "Determines how long a session lasts before being disconnected and requiring re-authorization.",
                    )}
                    required
                ></ak-text-input>

                <ak-form-group .expanded=${true}>
                    <span slot="header"> ${msg("Protocol settings")} </span>
                    <div slot="body" class="pf-c-form">
                        <ak-form-element-horizontal
                            label=${msg("Property mappings")}
                            ?required=${true}
                            name="propertyMappings"
                        >
                            <select class="pf-c-form-control" multiple>
                                ${this.propertyMappings?.results.map(
                                    (mapping) =>
                                        html`<option
                                            value=${ifDefined(mapping.pk)}
                                            ?selected=${selected.has(mapping.pk)}
                                        >
                                            ${mapping.name}
                                        </option>`,
                                )}
                            </select>
                            <p class="pf-c-form__helper-text">
                                ${msg("Hold control/command to select multiple items.")}
                            </p>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal label=${msg("Settings")} name="settings">
                            <ak-codemirror
                                mode="yaml"
                                value="${YAML.stringify(provider?.settings ?? {})}"
                            >
                            </ak-codemirror>
                            <p class="pf-c-form__helper-text">${msg("Connection settings.")}</p>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
            </form>`;
    }
}

export default ApplicationWizardAuthenticationByRAC;
