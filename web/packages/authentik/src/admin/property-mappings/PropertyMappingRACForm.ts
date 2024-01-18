import { first } from "@goauthentik/common/utils.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { docLink } from "@goauthentik/common/global.js";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { PropertymappingsApi, RACPropertyMapping } from "@goauthentik/api";

@customElement("ak-property-mapping-rac-form")
export class PropertyMappingLDAPForm extends ModelForm<RACPropertyMapping, string> {
    loadInstance(pk: string): Promise<RACPropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsRacRetrieve({
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

    async send(data: RACPropertyMapping): Promise<RACPropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsRacUpdate({
                pmUuid: this.instance.pk || "",
                rACPropertyMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsRacCreate({
                rACPropertyMappingRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("General settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Username")}
                        ?required=${true}
                        name="staticSettings.username"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.staticSettings.username)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Password")}
                        ?required=${true}
                        name="staticSettings.password"
                    >
                        <input
                            type="password"
                            value="${ifDefined(this.instance?.staticSettings.password)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("RDP settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="staticSettings.ignore-cert">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(
                                    this.instance?.staticSettings["ignore-cert"],
                                    false,
                                )}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Ignore server certificate")}</span
                            >
                        </label>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="staticSettings.enable-wallpaper">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(
                                    this.instance?.staticSettings["enable-wallpaper"],
                                    false,
                                )}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Enable wallpaper")}</span>
                        </label>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="staticSettings.enable-font-smoothing">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(
                                    this.instance?.staticSettings["enable-font-smoothing"],
                                    false,
                                )}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Enable font-smoothing")}</span>
                        </label>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="staticSettings.enable-full-window-drag">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(
                                    this.instance?.staticSettings["enable-full-window-drag"],
                                    false,
                                )}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Enable full window dragging")}</span
                            >
                        </label>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("Advanced settings")} </span>
                <div slot="body" class="pf-c-form">
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
                                href="${docLink(
                                    "/docs/property-mappings/expression?utm_source=authentik",
                                )}"
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
