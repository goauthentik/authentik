import "#components/ak-text-input";
import "#components/ak-switch-input";
import "#components/ak-number-input";
import "#elements/CodeMirror";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";
import { propertyMappingsProvider, propertyMappingsSelector } from "./RACProviderFormHelpers.js";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { deviceAccessGroupSource } from "#admin/common/search-sources";
import { AKAuthorizationFlowField } from "#admin/providers/components/flow-fields";

import { ProvidersApi, RACProvider } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-provider-rac-form")
export class RACProviderFormPage extends ModelForm<RACProvider, number> {
    protected endpoints = {
        load: (id: number) => aki(ProvidersApi).providersRacRetrieve({ id }),
        create: (rACProviderRequest: RACProvider) =>
            aki(ProvidersApi).providersRacCreate({ rACProviderRequest }),
        update: (id: number, rACProviderRequest: RACProvider) =>
            aki(ProvidersApi).providersRacUpdate({ id, rACProviderRequest }),
    };

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated provider.");
        }

        return msg("Successfully created provider.");
    }

    protected override renderForm(): TemplateResult {
        return html`
            <ak-text-input
                label=${msg("Provider Name")}
                required
                name="name"
                value="${ifDefined(this.instance?.name)}"
                placeholder=${msg("Type a provider name...")}
                spellcheck="false"
                ?autofocus=${!this.instance}
            ></ak-text-input>

            ${AKAuthorizationFlowField({ value: this.instance?.authorizationFlow })}
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
                    "When enabled, connection authorizations will be deleted when a client disconnects. This will force clients with flaky internet connections to re-authorize the device.",
                )}
            >
            </ak-switch-input>

            <ak-form-element-horizontal label=${msg("Device access group")} name="accessGroup">
                ${AKSearchSelect({
                    name: "accessGroup",
                    source: deviceAccessGroupSource,
                    value: this.instance?.accessGroup,
                    placeholder: msg("Select a device access group..."),
                })}
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Only devices in this access group can be accessed through this provider. Leave empty to allow every device the user has access to.",
                    )}
                </p>
            </ak-form-element-horizontal>

            <ak-form-group open label="${msg("Protocol settings")}">
                <div class="pf-c-form">
                    <ak-number-input
                        label=${msg("Maximum concurrent connections")}
                        name="maximumConnections"
                        required
                        value="${this.instance?.maximumConnections ?? 1}"
                        help=${msg(
                            "Maximum concurrent allowed connections to a single device. Can be set to -1 to disable the limit.",
                        )}
                    >
                    </ak-number-input>
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
