import "#components/ak-text-input";
import "#components/ak-number-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/FormGroup";
import "#admin/endpoints/ak-endpoints-device-group-search";

import { DEFAULT_CONFIG } from "#common/api/config";
import { dateTimeLocal } from "#common/temporal";

import { ModelForm } from "#elements/forms/ModelForm";
import { WithBrandConfig } from "#elements/mixins/branding";

import { EndpointsApi, EnrollmentToken, EnrollmentTokenRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-agent-enrollment-token-form")
export class EnrollmentTokenForm extends WithBrandConfig(ModelForm<EnrollmentToken, string>) {
    @property()
    connectorID?: string;

    @state()
    protected showExpiry = false;

    async loadInstance(pk: string): Promise<EnrollmentToken> {
        const token = await new EndpointsApi(
            DEFAULT_CONFIG,
        ).endpointsAgentsEnrollmentTokensRetrieve({
            tokenUuid: pk,
        });
        this.showExpiry = token.expiring ?? false;
        return token;
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

    renderExpiry() {
        return html`<ak-form-element-horizontal label=${msg("Expires on")} name="expires">
            <input
                type="datetime-local"
                data-type="datetime-local"
                value="${dateTimeLocal(this.instance?.expires ?? new Date())}"
                class="pf-c-form-control"
            />
        </ak-form-element-horizontal>`;
    }

    renderForm() {
        return html`<ak-text-input
                name="name"
                placeholder=${msg("Token name...")}
                label=${msg("Token name")}
                value=${ifDefined(this.instance?.name)}
                required
            ></ak-text-input>
            <ak-form-element-horizontal label=${msg("Device Access Group")} name="deviceGroup">
                <ak-endpoints-device-group-search
                    .group=${this.instance?.deviceGroup}
                ></ak-endpoints-device-group-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Select a group for the device to be added to upon enrollment.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="expiring">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.expiring ?? false}
                        @change=${(ev: Event) => {
                            const el = ev.target as HTMLInputElement;
                            this.showExpiry = el.checked;
                        }}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Expiring")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "If this is selected, the token will expire. Upon expiration, the token will be rotated.",
                    )}
                </p>
            </ak-form-element-horizontal>
            ${this.showExpiry ? this.renderExpiry() : nothing}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-agent-enrollment-token-form": EnrollmentTokenForm;
    }
}
