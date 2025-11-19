import "#components/ak-text-input";
import "#components/ak-number-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/FormGroup";
import "#admin/endpoints/ak-endpoints-device-group-search";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";
import { WithBrandConfig } from "#elements/mixins/branding";

import { EndpointsApi, EnrollmentToken, EnrollmentTokenRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-agent-enrollment-token-form")
export class EnrollmentTokenForm extends WithBrandConfig(ModelForm<EnrollmentToken, string>) {
    @property()
    connectorID?: string;

    loadInstance(pk: string): Promise<EnrollmentToken> {
        return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsEnrollmentTokensRetrieve({
            tokenUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated token.")
            : msg("Successfully created token.");
    }

    async send(data: EnrollmentToken): Promise<EnrollmentToken> {
        if (!this.instance) {
            data.connector = this.connectorID || "";
        } else {
            data.connector = this.instance.connector;
        }
        if (this.instance) {
            return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsEnrollmentTokensPartialUpdate({
                tokenUuid: this.instance.tokenUuid,
                patchedEnrollmentTokenRequest: data,
            });
        }
        return new EndpointsApi(DEFAULT_CONFIG).endpointsAgentsEnrollmentTokensCreate({
            enrollmentTokenRequest: data as unknown as EnrollmentTokenRequest,
        });
    }

    renderForm() {
        return html`<ak-text-input
                name="name"
                placeholder=${msg("Token name...")}
                label=${msg("Token name")}
                value=${ifDefined(this.instance?.name)}
                required
            ></ak-text-input>
            <ak-form-element-horizontal label=${msg("Device Group")} name="deviceGroup">
                <ak-endpoints-device-group-search
                    .group=${this.instance?.deviceGroup}
                ></ak-endpoints-device-group-search>
            </ak-form-element-horizontal> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-agent-enrollment-token-form": EnrollmentTokenForm;
    }
}
