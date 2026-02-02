import "#elements/forms/HorizontalFormElement";
import "#elements/forms/FormGroup";
import "#components/ak-text-input";
import "#components/ak-number-input";
import "#components/ak-switch-input";
import "#admin/endpoints/ak-endpoints-device-group-search";

import { DEFAULT_CONFIG } from "#common/api/config";
import { dateTimeLocal } from "#common/temporal";

import { ModelForm } from "#elements/forms/ModelForm";
import { WithBrandConfig } from "#elements/mixins/branding";

import { AKLabel } from "#components/ak-label";

import { EndpointsApi, EnrollmentToken, EnrollmentTokenRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const EXPIRATION_DURATION = 30 * 60 * 1000; // 30 minutes

/**
 * Enrollment Token Form
 *
 * @prop {string} instancePk - The primary key of the instance to load.
 */
@customElement("ak-endpoints-agent-enrollment-token-form")
export class EnrollmentTokenForm extends WithBrandConfig(ModelForm<EnrollmentToken, string>) {
    protected expirationMinimumDate = new Date();

    @state()
    protected expiresAt: Date | null = new Date(Date.now() + EXPIRATION_DURATION);

    @property({ type: String, attribute: "connector-id" })
    public connectorID?: string;

    public override reset(): void {
        super.reset();

        this.expiresAt = new Date(Date.now() + EXPIRATION_DURATION);
    }

    async loadInstance(pk: string): Promise<EnrollmentToken> {
        const token = await new EndpointsApi(
            DEFAULT_CONFIG,
        ).endpointsAgentsEnrollmentTokensRetrieve({
            tokenUuid: pk,
        });

        this.expiresAt = token.expiring
            ? new Date(token.expires || Date.now() + EXPIRATION_DURATION)
            : null;

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

    //#region Event Listeners

    #expiringChangeListener = (event: Event) => {
        const expiringElement = event.target as HTMLInputElement;

        if (!expiringElement.checked) {
            this.expiresAt = null;
            return;
        }

        if (this.instance?.expiring && this.instance.expires) {
            this.expiresAt = new Date(this.instance.expires);
            return;
        }

        this.expiresAt = new Date(Date.now() + EXPIRATION_DURATION);
    };

    //#endregion

    //#region Rendering

    renderForm() {
        return html`<ak-text-input
                name="name"
                placeholder=${msg("Type a name for the token...")}
                label=${msg("Token name")}
                value=${ifDefined(this.instance?.name)}
                required
                ?autofocus=${!this.instance}
            ></ak-text-input>
            <ak-form-element-horizontal label=${msg("Device Access Group")} name="deviceGroup">
                <ak-endpoints-device-group-search
                    .group=${this.instance?.deviceGroup}
                ></ak-endpoints-device-group-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Select a device access group to be added to upon enrollment.")}
                </p>
            </ak-form-element-horizontal>

            <ak-switch-input
                name="expiring"
                label=${msg("Expiring")}
                help=${msg(
                    "Whether the token will expire. Upon expiration, the token will be rotated.",
                )}
                @change=${this.#expiringChangeListener}
                ?checked=${this.expiresAt}
            ></ak-switch-input>

            <ak-form-element-horizontal name="expires">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "expiration-date-input",
                    },
                    msg("Expires on"),
                )}

                <input
                    id="expiration-date-input"
                    type="datetime-local"
                    value=${this.expiresAt ? dateTimeLocal(this.expiresAt) : ""}
                    min=${dateTimeLocal(this.expirationMinimumDate)}
                    ?disabled=${!this.expiresAt}
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal> `;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-agent-enrollment-token-form": EnrollmentTokenForm;
    }
}
