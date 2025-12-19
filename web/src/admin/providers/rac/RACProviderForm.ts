import "#admin/common/ak-flow-search/ak-flow-search";
import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-branded-flow-search";
import "#components/ak-switch-input";
import "#elements/CodeMirror";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";

import { propertyMappingsProvider, propertyMappingsSelector } from "./RACProviderFormHelpers.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { FlowsInstancesListDesignationEnum, ProvidersApi, RACProvider } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-provider-rac-form")
export class RACProviderFormPage extends ModelForm<RACProvider, number> {
    async loadInstance(pk: number): Promise<RACProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersRacRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated provider.");
        }
        return msg("Successfully created provider.");
    }

    async send(data: RACProvider): Promise<RACProvider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersRacUpdate({
                id: this.instance.pk,
                rACProviderRequest: data,
            });
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersRacCreate({
            rACProviderRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Provider Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                    placeholder=${msg("Type a provider name...")}
                    spellcheck="false"
                />
            </ak-form-element-horizontal>

            <ak-form-element-horizontal
                name="authorizationFlow"
                label=${msg("Authorization flow")}
                required
            >
                <ak-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authorization}
                    .currentFlow=${this.instance?.authorizationFlow}
                    required
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when authorizing this provider.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Connection expiry")}
                required
                name="connectionExpiry"
            >
                <input
                    type="text"
                    value="${this.instance?.connectionExpiry ?? "hours=8"}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Determines how long a session lasts before being disconnected and requiring re-authorization.",
                    )}
                </p>
                <ak-utils-time-delta-help></ak-utils-time-delta-help>
            </ak-form-element-horizontal>
            <ak-switch-input
                name="deleteTokenOnDisconnect"
                label=${msg("Delete authorization on disconnect")}
                ?checked=${this.instance?.deleteTokenOnDisconnect ?? false}
                help=${msg(
                    "When enabled, connection authorizations will be deleted when a client disconnects. This will force clients with flaky internet connections to re-authorize the endpoint.",
                )}
            >
            </ak-switch-input>

            <ak-form-group open label="${msg("Protocol settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Property mappings")}
                        name="propertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(this.instance?.propertyMappings)}
                            available-label="${msg("Available Property Mappings")}"
                            selected-label="${msg("Selected Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Settings")} name="settings">
                        <ak-codemirror
                            mode="yaml"
                            value="${YAML.stringify(this.instance?.settings ?? {})}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">${msg("Connection settings.")}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-rac-form": RACProviderFormPage;
    }
}
