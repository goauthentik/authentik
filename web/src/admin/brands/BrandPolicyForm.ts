import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { CodeMirrorMode } from "#elements/CodeMirror";
import { ModelForm } from "#elements/forms/ModelForm";

import {
    Brand,
    BrandPolicy,
    CoreApi,
    CoreBrandsListRequest,
    PolicyEngineMode,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-brand-policy-form")
export class BrandPolicyForm extends ModelForm<BrandPolicy, string> {
    loadInstance(pbmUuid: string): Promise<BrandPolicy> {
        return new CoreApi(DEFAULT_CONFIG).coreBrandPoliciesRetrieve({
            pbmUuid,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated brand policy.")
            : msg("Successfully created brand policy.");
    }

    async send(data: BrandPolicy): Promise<BrandPolicy> {
        if (this.instance?.pbmUuid) {
            return new CoreApi(DEFAULT_CONFIG).coreBrandPoliciesPartialUpdate({
                pbmUuid: this.instance.pbmUuid,
                patchedBrandPolicyRequest: data,
            });
        }
        return new CoreApi(DEFAULT_CONFIG).coreBrandPoliciesCreate({
            brandPolicyRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Brand")} required name="brand">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Brand[]> => {
                        const args: CoreBrandsListRequest = {
                            ordering: "domain",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const brands = await new CoreApi(DEFAULT_CONFIG).coreBrandsList(args);
                        return brands.results;
                    }}
                    .renderElement=${(brand: Brand): string => {
                        return brand.domain;
                    }}
                    .value=${(brand: Brand | undefined): string | undefined => {
                        return brand?.brandUuid;
                    }}
                    .selected=${(brand: Brand): boolean => {
                        return this.instance?.brand === brand.brandUuid;
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Path")} required name="path">
                <input
                    type="text"
                    value="${this.instance?.path ?? ""}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Regex. If a request's path matches this, the policies will run. E.g. ^/api/v[\\d+]/rbac/",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Policy engine mode")}
                required
                name="policyEngineMode"
            >
                <ak-radio
                    .options=${[
                        {
                            label: "any",
                            value: PolicyEngineMode.Any,
                            default: true,
                            description: html`${msg("Any policy must match to grant access")}`,
                        },
                        {
                            label: "all",
                            value: PolicyEngineMode.All,
                            description: html`${msg("All policies must match to grant access")}`,
                        },
                    ]}
                    .value=${this.instance?.policyEngineMode}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Failure HTTP Status")}
                required
                name="failureHttpStatusCode"
            >
                <input
                    type="text"
                    inputmode="numeric"
                    value="${this.instance?.failureHttpStatusCode ?? ""}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Failure Response")} name="failureResponse">
                <ak-codemirror
                    mode=${CodeMirrorMode.Python}
                    value=${this.instance?.failureResponse ?? ""}
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "If this field contains valid JSON, it will be returned as application/json, otherwise, it will be returned as text/html.",
                    )}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-brand-policy-form": BrandPolicyForm;
    }
}
