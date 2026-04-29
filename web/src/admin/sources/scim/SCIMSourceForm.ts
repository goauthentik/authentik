import "#components/ak-slug-input";
import "#components/ak-text-input";
import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { propertyMappingsProvider, propertyMappingsSelector } from "./SCIMSourceFormHelpers.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { placeholderHelperText } from "#admin/helperText";
import { BaseSourceForm } from "#admin/sources/BaseSourceForm";

import { SCIMSource, SCIMSourceRequest, SourcesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-source-scim-form")
export class SCIMSourceForm extends BaseSourceForm<SCIMSource> {
    async loadInstance(pk: string): Promise<SCIMSource> {
        return new SourcesApi(DEFAULT_CONFIG)
            .sourcesScimRetrieve({
                slug: pk,
            })
            .then((source) => {
                return source;
            });
    }

    async send(data: SCIMSource): Promise<SCIMSource> {
        if (this.instance?.slug) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesScimPartialUpdate({
                slug: this.instance.slug,
                patchedSCIMSourceRequest: data,
            });
        }
        return new SourcesApi(DEFAULT_CONFIG).sourcesScimCreate({
            sCIMSourceRequest: data as unknown as SCIMSourceRequest,
        });
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                label=${msg("Source Name")}
                placeholder=${msg("Type a name for this source...")}
                required
                name="name"
                value="${ifDefined(this.instance?.name)}"
            ></ak-text-input>
            <ak-slug-input
                name="slug"
                placeholder=${msg("e.g. my-scim-source")}
                value=${ifDefined(this.instance?.slug)}
                label=${msg("Slug")}
                required
                input-hint="code"
            ></ak-slug-input>
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
            ></ak-switch-input>

            <ak-form-group open label="${msg("SCIM Attribute mapping")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User Property Mappings")}
                        name="userPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.userPropertyMappings,
                            )}
                            available-label="${msg("Available User Property Mappings")}"
                            selected-label="${msg("Selected User Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for user creation.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group Property Mappings")}
                        name="groupPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${propertyMappingsSelector(
                                this.instance?.groupPropertyMappings,
                            )}
                            available-label="${msg("Available Group Property Mappings")}"
                            selected-label="${msg("Selected Group Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for group creation.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Advanced protocol settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("User path")} name="userPathTemplate">
                        <input
                            type="text"
                            value="${this.instance?.userPathTemplate ??
                            "goauthentik.io/sources/%(slug)s"}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">${placeholderHelperText}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-scim-form": SCIMSourceForm;
    }
}
