import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Interface, InterfaceTypeEnum, InterfacesApi } from "@goauthentik/api";

@customElement("ak-interface-form")
export class InterfaceForm extends ModelForm<Interface, string> {
    loadInstance(pk: string): Promise<Interface> {
        return new InterfacesApi(DEFAULT_CONFIG).interfacesRetrieve({
            interfaceUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated interface.`;
        } else {
            return t`Successfully created interface.`;
        }
    }

    send = (data: Interface): Promise<Interface> => {
        if (this.instance?.interfaceUuid) {
            return new InterfacesApi(DEFAULT_CONFIG).interfacesUpdate({
                interfaceUuid: this.instance.interfaceUuid,
                interfaceRequest: data,
            });
        } else {
            return new InterfacesApi(DEFAULT_CONFIG).interfacesCreate({
                interfaceRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`URL Name`} ?required=${true} name="urlName">
                <input
                    type="text"
                    value="${first(this.instance?.urlName, "")}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Name used in the URL when accessing this interface.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Type`} ?required=${true} name="type">
                <ak-radio
                    .options=${[
                        {
                            label: t`Enduser interface`,
                            value: InterfaceTypeEnum.User,
                            default: true,
                        },
                        {
                            label: t`Flow interface`,
                            value: InterfaceTypeEnum.Flow,
                        },
                        {
                            label: t`Admin interface`,
                            value: InterfaceTypeEnum.Admin,
                        },
                    ]}
                    .value=${this.instance?.type}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${t`Configure how authentik will use this interface.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Template`} ?required=${true} name="template"
                ><ak-codemirror
                    mode="html"
                    value="${ifDefined(this.instance?.template)}"
                ></ak-codemirror>
            </ak-form-element-horizontal>
        </form>`;
    }
}
