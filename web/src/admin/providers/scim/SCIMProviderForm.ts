import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import {
    SCIMProvider,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-provider-scim-form")
export class SCIMProviderFormPage extends ModelForm<SCIMProvider, number> {
    loadInstance(pk: number): Promise<SCIMProvider> {
        return new ProvidersApi(DEFAULT_CONFIG).providersScimRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated provider.`;
        } else {
            return t`Successfully created provider.`;
        }
    }

    send = (data: SCIMProvider): Promise<SCIMProvider> => {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersScimUpdate({
                id: this.instance.pk || 0,
                sCIMProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersScimCreate({
                sCIMProviderRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Protocol settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`URL`} ?required=${true} name="url">
                        <input
                            type="text"
                            value="${first(this.instance?.url, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`SCIM base url, usually ends in /v2.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Token`} ?required=${true} name="token">
                        <input
                            type="text"
                            value="${first(this.instance?.token, "")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Token to authenticate with. Currently only bearer authentication is supported.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
