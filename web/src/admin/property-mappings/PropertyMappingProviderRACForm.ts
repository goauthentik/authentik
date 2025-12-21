import "#elements/CodeMirror";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";

import { DEFAULT_CONFIG } from "#common/api/config";
import { docLink } from "#common/global";

import type { RadioOption } from "#elements/forms/Radio";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, RACPropertyMapping } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

export const staticSettingOptions: RadioOption<string | undefined>[] = [
    {
        label: msg("Unconfigured"),
        value: undefined,
        default: true,
        description: html`${msg("This option will not be changed by this mapping.")}`,
    },
    {
        label: msg("Enabled"),
        value: "true",
    },
    {
        label: msg("Disabled"),
        value: "false",
    },
];

@customElement("ak-property-mapping-provider-rac-form")
export class PropertyMappingProviderRACForm extends BasePropertyMappingForm<RACPropertyMapping> {
    loadInstance(pk: string): Promise<RACPropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderRacRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: RACPropertyMapping): Promise<RACPropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderRacUpdate({
                pmUuid: this.instance.pk,
                rACPropertyMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderRacCreate({
            rACPropertyMappingRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("General settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Username")}
                        name="staticSettings.username"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.staticSettings.username)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Password")}
                        name="staticSettings.password"
                    >
                        <input
                            type="password"
                            value="${ifDefined(this.instance?.staticSettings.password)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("RDP settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Ignore server certificate")}
                        name="staticSettings.ignore-cert"
                    >
                        <ak-radio
                            .options=${staticSettingOptions}
                            .value=${this.instance?.staticSettings["ignore-cert"]}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enable wallpaper")}
                        name="staticSettings.enable-wallpaper"
                    >
                        <ak-radio
                            .options=${staticSettingOptions}
                            .value=${this.instance?.staticSettings["enable-wallpaper"]}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enable font-smoothing")}
                        name="staticSettings.enable-font-smoothing"
                    >
                        <ak-radio
                            .options=${staticSettingOptions}
                            .value=${this.instance?.staticSettings["enable-font-smoothing"]}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enable full window dragging")}
                        name="staticSettings.enable-full-window-drag"
                    >
                        <ak-radio
                            .options=${staticSettingOptions}
                            .value=${this.instance?.staticSettings["enable-full-window-drag"]}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Advanced settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Expression")} name="expression">
                        <ak-codemirror
                            mode="python"
                            value="${ifDefined(this.instance?.expression)}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Expression using Python.")}
                            <a
                                target="_blank"
                                rel="noopener noreferrer"
                                href=${docLink(
                                    "/add-secure-apps/providers/property-mappings/expression",
                                )}
                            >
                                ${msg("See documentation for a list of all variables.")}
                            </a>
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-rac-form": PropertyMappingProviderRACForm;
    }
}
