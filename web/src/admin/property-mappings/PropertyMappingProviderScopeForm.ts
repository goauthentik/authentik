import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, ScopeMapping } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-property-mapping-provider-scope-form")
export class PropertyMappingProviderScopeForm extends BasePropertyMappingForm<ScopeMapping> {
    loadInstance(pk: string): Promise<ScopeMapping> {
        return aki(PropertymappingsApi).propertymappingsProviderScopeRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: ScopeMapping): Promise<ScopeMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsProviderScopeUpdate({
                pmUuid: this.instance.pk,
                scopeMappingRequest: data,
            });
        }

        return aki(PropertymappingsApi).propertymappingsProviderScopeCreate({
            scopeMappingRequest: data,
        });
    }

    renderExtraFields(): TemplateResult {
        return html` <ak-form-element-horizontal
                label=${msg("Scope name")}
                required
                name="scopeName"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.scopeName)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Scope which the client can specify to access these properties.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Description")} name="description">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.description)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Description shown to the user when consenting. If left empty, the user won't be informed.",
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-scope-form": PropertyMappingProviderScopeForm;
    }
}
