import "#elements/CodeMirror";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";

import { DEFAULT_CONFIG } from "#common/api/config";
import { docLink } from "#common/global";

import type { RadioOption } from "#elements/forms/Radio";

import { AKLabel } from "#components/ak-label";

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

    protected override renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal required name="name">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "name",
                        required: true,
                    },
                    msg("Name"),
                )}
                <input
                    id="name"
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("General settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="staticSettings.username">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "staticSettings.username",
                            },
                            msg("Username"),
                        )}
                        <input
                            id="staticSettings.username"
                            type="text"
                            value="${ifDefined(this.instance?.staticSettings.username)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="staticSettings.password">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "staticSettings.password",
                            },
                            msg("Password"),
                        )}
                        <input
                            id="staticSettings.password"
                            type="password"
                            value="${ifDefined(this.instance?.staticSettings.password)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("RDP settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="staticSettings.ignore-cert">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "staticSettings.ignore-cert",
                            },
                            msg("Ignore server certificate"),
                        )}
                        <ak-radio
                            id="staticSettings.ignore-cert"
                            .options=${staticSettingOptions}
                            .value=${this.instance?.staticSettings["ignore-cert"]}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="staticSettings.enable-wallpaper">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "staticSettings.enable-wallpaper",
                            },
                            msg("Enable wallpaper"),
                        )}
                        <ak-radio
                            id="staticSettings.enable-wallpaper"
                            .options=${staticSettingOptions}
                            .value=${this.instance?.staticSettings["enable-wallpaper"]}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="staticSettings.enable-font-smoothing">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "staticSettings.enable-font-smoothing",
                            },
                            msg("Enable font-smoothing"),
                        )}
                        <ak-radio
                            id="staticSettings.enable-font-smoothing"
                            .options=${staticSettingOptions}
                            .value=${this.instance?.staticSettings["enable-font-smoothing"]}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="staticSettings.enable-full-window-drag">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "staticSettings.enable-full-window-drag",
                            },
                            msg("Enable full window dragging"),
                        )}
                        <ak-radio
                            id="staticSettings.enable-full-window-drag"
                            .options=${staticSettingOptions}
                            .value=${this.instance?.staticSettings["enable-full-window-drag"]}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group label="${msg("Advanced settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal name="expression">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "expression",
                            },
                            msg("Expression"),
                        )}
                        <ak-codemirror
                            id="expression"
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
