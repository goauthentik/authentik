import { placeholderHelperText } from "@goauthentik/admin/helperText";
import { BaseSourceForm } from "@goauthentik/admin/sources/BaseSourceForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-slug-input.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { SCIMSource, SCIMSourceRequest, SourcesApi } from "@goauthentik/api";

import { propertyMappingsProvider, propertyMappingsSelector } from "./SCIMSourceFormHelpers.js";

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

            <ak-slug-input
                name="slug"
                value=${ifDefined(this.instance?.slug)}
                label=${msg("Slug")}
                required
                input-hint="code"
            ></ak-slug-input>

            <ak-form-element-horizontal name="enabled">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${this.instance?.enabled ?? true}
                    />
                    <label class="pf-c-check__label"> ${msg("Enabled")} </label>
                </div>
            </ak-form-element-horizontal>
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
            </ak-form-group>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-scim-form": SCIMSourceForm;
    }
}
