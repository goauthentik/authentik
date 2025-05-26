import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-branded-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { FlowsInstancesListDesignationEnum, ProvidersApi, RACProvider } from "@goauthentik/api";

import { propertyMappingsProvider, propertyMappingsSelector } from "./RACProviderFormHelpers.js";

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
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>

            <ak-form-element-horizontal
                name="authorizationFlow"
                label=${msg("Authorization flow")}
                ?required=${true}
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
                ?required=${true}
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
            <ak-form-element-horizontal name="deleteTokenOnDisconnect">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.deleteTokenOnDisconnect ?? false}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label"
                        >${msg("Delete authorization on disconnect")}</span
                    >
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When enabled, connection authorizations will be deleted when a client disconnects. This will force clients with flaky internet connections to re-authorize the endpoint.",
                    )}
                </p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
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
