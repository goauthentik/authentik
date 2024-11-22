import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import "@goauthentik/elements/ak-array-input.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { css } from "lit";
import { customElement, state } from "lit/decorators.js";

import { ClientTypeEnum, OAuth2Provider, ProvidersApi } from "@goauthentik/api";

import { renderForm } from "./OAuth2ProviderFormForm.js";

/**
 * Form page for OAuth2 Authentication Method
 *
 * @element ak-provider-oauth2-form
 *
 */

@customElement("ak-provider-oauth2-form")
export class OAuth2ProviderFormPage extends BaseProviderForm<OAuth2Provider> {
    @state()
    showClientSecret = true;

    static get styles() {
        return super.styles.concat(css`
            ak-array-input {
                width: 100%;
            }
        `);
    }

    async loadInstance(pk: number): Promise<OAuth2Provider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersOauth2Retrieve({
            id: pk,
        });
        this.showClientSecret = provider.clientType === ClientTypeEnum.Confidential;
        return provider;
    }

    async send(data: OAuth2Provider): Promise<OAuth2Provider> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersOauth2Update({
                id: this.instance.pk,
                oAuth2ProviderRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersOauth2Create({
                oAuth2ProviderRequest: data,
            });
        }
    }

    renderForm() {
        const showClientSecretCallback = (show: boolean) => {
            this.showClientSecret = show;
        };
        return renderForm(this.instance ?? {}, [], this.showClientSecret, showClientSecretCallback);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-oauth2-form": OAuth2ProviderFormPage;
    }
}
