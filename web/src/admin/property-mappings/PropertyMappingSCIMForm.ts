import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { PropertymappingsApi, SCIMMapping } from "@goauthentik/api";

@customElement("ak-property-mapping-scim-form")
export class PropertyMappingSCIMForm extends ModelForm<SCIMMapping, string> {
    loadInstance(pk: string): Promise<SCIMMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScimRetrieve({
            pmUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated mapping.");
        } else {
            return msg("Successfully created mapping.");
        }
    }

    async send(data: SCIMMapping): Promise<SCIMMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScimUpdate({
                pmUuid: this.instance.pk || "",
                sCIMMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScimCreate({
                sCIMMappingRequest: data,
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
                <ak-codemirror mode="python" value="${ifDefined(this.instance?.expression)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Expression using Python.")}
                    <a
                        target="_blank"
                        href="${docLink("/docs/property-mappings/expression?utm_source=authentik")}"
                    >
                        ${msg("See documentation for a list of all variables.")}
                    </a>
                </p>
            </ak-form-element-horizontal>`;
    }
}
