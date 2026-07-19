import { renderForm } from "./OAuth2DCRFormForm.js";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { OAuth2DynamicClientRegistration, ProvidersApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

/**
 * Form page for OAuth2 Dynamic Client Registration configuration
 *
 * @element ak-provider-oauth2-dcr-form
 *
 */
@customElement("ak-provider-oauth2-dcr-form")
export class OAuth2DCRForm extends ModelForm<OAuth2DynamicClientRegistration, string> {
    public static override verboseName = msg("Dynamic Client Registration");
    public static override verboseNamePlural = msg("Dynamic Client Registration");

    /**
     * The provider this configuration is (or will be) attached to.
     * Only used when creating a new configuration.
     */
    @property({ type: Number })
    public providerID: number | null = null;

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated Dynamic Client Registration.")
            : msg("Successfully enabled Dynamic Client Registration.");
    }

    protected override loadInstance(pk: string): Promise<OAuth2DynamicClientRegistration> {
        return aki(ProvidersApi).providersOauth2DcrRetrieve({
            pbmUuid: pk,
        });
    }

    public override async send(
        data: OAuth2DynamicClientRegistration,
    ): Promise<OAuth2DynamicClientRegistration> {
        if (this.instance) {
            return aki(ProvidersApi).providersOauth2DcrUpdate({
                pbmUuid: this.instance.pbmUuid,
                oAuth2DynamicClientRegistrationRequest: data,
            });
        }
        data.provider = this.providerID || 0;
        return aki(ProvidersApi).providersOauth2DcrCreate({
            oAuth2DynamicClientRegistrationRequest: data,
        });
    }

    protected override renderForm(): SlottedTemplateResult {
        return renderForm({ dcr: this.instance });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-oauth2-dcr-form": OAuth2DCRForm;
    }
}
