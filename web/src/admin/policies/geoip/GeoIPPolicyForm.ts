import { BasePolicyForm } from "@goauthentik/admin/policies/BasePolicyForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/ak-dual-select";
import { DataProvision, DualSelectPair } from "@goauthentik/elements/ak-dual-select/types";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { DetailedCountry, GeoIPPolicy, PoliciesApi } from "@goauthentik/api";

import { countryCache } from "./CountryCache";

function countryToPair(country: DetailedCountry): DualSelectPair {
    return [country.code, country.name];
}

@customElement("ak-policy-geoip-form")
export class GeoIPPolicyForm extends BasePolicyForm<GeoIPPolicy> {
    loadInstance(pk: string): Promise<GeoIPPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesGeoipRetrieve({
            policyUuid: pk,
        });
    }

    async send(data: GeoIPPolicy): Promise<GeoIPPolicy> {
        if (data.asns?.toString() === "") {
            data.asns = [];
        } else {
            data.asns = (data.asns as unknown as string).split(",").map(Number);
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
                    "Ensure the user satisfies requirements of geography or network topology, based on IP address. If any of the configured values match, the policy passes.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.executionLogging ?? false}
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
                    <ak-form-element-horizontal label=${msg("ASNs")} name="asns">
                        <input
                            type="text"
                            value="${this.instance?.asns ?? ""}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "List of autonomous system numbers. Comma separated. E.g. 13335, 15169, 20940",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Countries")} name="countries">
                        <ak-dual-select-provider
                            .provider=${(page: number, search?: string): Promise<DataProvision> => {
                                return countryCache
                                    .getCountries()
                                    .then((results) => {
                                        if (!search) return results;
                                        return results.filter((result) =>
                                            result.name
                                                .toLowerCase()
                                                .includes(search.toLowerCase()),
                                        );
                                    })
                                    .then((results) => {
                                        return {
                                            options: results.map(countryToPair),
                                        };
                                    });
                            }}
                            .selected=${(this.instance?.countriesObj ?? []).map(countryToPair)}
                            available-label="${msg("Available Countries")}"
                            selected-label="${msg("Selected Countries")}"
                        >
                        </ak-dual-select-provider>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}
