import { BaseProviderForm } from "@goauthentik/admin/providers/BaseProviderForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types";

import { css } from "lit";
import { customElement, state } from "lit/decorators.js";

import { ClientTypeEnum, OAuth2Provider, ProvidersApi } from "@goauthentik/api";

import { renderForm } from "./OAuth2ProviderFormForm.js";

const providerToSelect = (provider: OAuth2Provider) => [provider.pk, provider.name];

export async function oauth2ProvidersProvider(page = 1, search = "") {
    const oauthProviders = await new ProvidersApi(DEFAULT_CONFIG).providersOauth2List({
        ordering: "name",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: oauthProviders.pagination,
        options: oauthProviders.results.map((provider) => providerToSelect(provider)),
    };
}

export function oauth2ProviderSelector(instanceProviders: number[] | undefined) {
    if (!instanceProviders) {
        return async (mappings: DualSelectPair<OAuth2Provider>[]) =>
            mappings.filter(
                ([_0, _1, _2, source]: DualSelectPair<OAuth2Provider>) => source !== undefined,
            );
    }

    return async () => {
        const oauthSources = new ProvidersApi(DEFAULT_CONFIG);
        const mappings = await Promise.allSettled(
            instanceProviders.map((instanceId) =>
                oauthSources.providersOauth2Retrieve({ id: instanceId }),
            ),
        );

        return mappings
            .filter((s) => s.status === "fulfilled")
            .map((s) => s.value)
            .map(providerToSelect);
    };
}

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
