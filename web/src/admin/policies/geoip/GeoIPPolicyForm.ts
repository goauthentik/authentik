import { BasePolicyForm } from "@goauthentik/admin/policies/BasePolicyForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { App, GeoIPPolicy, PoliciesApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-policy-geoip-form")
export class GeoIPPolicyForm extends BasePolicyForm<GeoIPPolicy> {
    loadInstance(pk: string): Promise<GeoIPPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesGeoipRetrieve({
            policyUuid: pk,
        });
    }

    async send(data: GeoIPPolicy): Promise<GeoIPPolicy> {
        if (data.asnMode?.toString() === "") {
            data.asnMode = "block";
        }

        if (data.asnList?.toString() === "") {
            data.asnList = [];
        } else {
            data.asnList = data.asnList.split(",").map(Number);
        }

        if (data.countryMode?.toString() === "") {
            data.countryMode = "block";
        }

        if (data.countryList?.toString() === "") {
            data.countryList = [];
        } else {
            data.countryList = data.countryList.split(",");
        }

        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesGeoipUpdate({
                policyUuid: this.instance.pk || "",
                geoIPPolicyRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesGeoipCreate({
                geoIPPolicyRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Ensure the user satisfies requirements of geography or network topology, based on IP address.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.executionLogging, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Execution logging")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Policy-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("ASN Mode")} name="asnMode">
                        <ak-search-select
                            .fetchObjects=${async () => {
                                return [
                                    { name: "allow", label: "Allow" },
                                    { name: "block", label: "Block" },
                                ];
                            }}
                            .renderElement=${(item: TypeCreate): string => {
                                return item.label;
                            }}
                            .value=${(item: TypeCreate | undefined): string | undefined => {
                                return item.name;
                            }}
                            .selected=${(item: TypeCreate): boolean => {
                                return this.instance?.asnMode === item.name;
                            }}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Block or only allow connections from IPs from the provided autonomous systems.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("ASN List")} name="asnList">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.asnList || "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "List of autonomous system numbers. Comma separated. E.g. 13335,15169,20940",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Country Mode")} name="countryMode">
                        <ak-search-select
                            .fetchObjects=${async () => {
                                return [
                                    { name: "allow", label: "Allow" },
                                    { name: "block", label: "Block" },
                                ];
                            }}
                            .renderElement=${(item: App): string => {
                                return item.label;
                            }}
                            .value=${(item: App | undefined): string | undefined => {
                                return item.name;
                            }}
                            .selected=${(item: App): boolean => {
                                return this.instance?.countryMode === item.name;
                            }}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Block or only allow connections from IPs from the provided countries.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Country List")} name="countryList">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.countryList || "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "List of ISO-3166-1 alpha-2 country codes. Comma separated. E.g. NO,DK,SE",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}
