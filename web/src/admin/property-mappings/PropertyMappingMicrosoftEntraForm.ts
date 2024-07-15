import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { MicrosoftEntraProviderMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-microsoft-entra-form")
export class PropertyMappingMicrosoftEntraForm extends BasePropertyMappingForm<MicrosoftEntraProviderMapping> {
    loadInstance(pk: string): Promise<MicrosoftEntraProviderMapping> {
        return new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsProviderMicrosoftEntraRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: MicrosoftEntraProviderMapping): Promise<MicrosoftEntraProviderMapping> {
        if (this.instance) {
            return new PropertymappingsApi(
                DEFAULT_CONFIG,
            ).propertymappingsProviderMicrosoftEntraUpdate({
                pmUuid: this.instance.pk,
                microsoftEntraProviderMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(
                DEFAULT_CONFIG,
            ).propertymappingsProviderMicrosoftEntraCreate({
                microsoftEntraProviderMappingRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Expression")}
                ?required=${true}
                name="expression"
            >
                <ak-codemirror
                    mode=${CodeMirrorMode.Python}
                    value="${ifDefined(this.instance?.expression)}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Expression using Python.")}
                    <a
                        target="_blank"
                        rel="noopener noreferrer"
                        href="${docLink("/docs/property-mappings/expression?utm_source=authentik")}"
                    >
                        ${msg("See documentation for a list of all variables.")}
                    </a>
                </p>
            </ak-form-element-horizontal>`;
    }
}
