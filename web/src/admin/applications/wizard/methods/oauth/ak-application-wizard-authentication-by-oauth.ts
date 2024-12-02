import { renderForm } from "@goauthentik/admin/providers/oauth2/OAuth2ProviderFormForm.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

import { SourcesApi } from "@goauthentik/api";
import { type OAuth2Provider, type PaginatedOAuthSourceList } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-oauth")
export class ApplicationWizardAuthenticationByOauth extends BaseProviderPanel {
    @state()
    showClientSecret = true;

    @state()
    oauthSources?: PaginatedOAuthSourceList;

    constructor() {
        super();
        new SourcesApi(DEFAULT_CONFIG)
            .sourcesOauthList({
                ordering: "name",
                hasJwks: true,
            })
            .then((oauthSources: PaginatedOAuthSourceList) => {
                this.oauthSources = oauthSources;
            });
    }

    render() {
        const provider = this.wizard.provider as OAuth2Provider | undefined;
        const errors = this.wizard.errors.provider;
        const showClientSecretCallback = (show: boolean) => {
            this.showClientSecret = show;
        };
        return html` <ak-wizard-title>${msg("Configure OAuth2 Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                ${renderForm(
                    provider ?? {},
                    errors,
                    this.showClientSecret,
                    showClientSecretCallback,
                )}
            </form>`;
    }
}

export default ApplicationWizardAuthenticationByOauth;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-by-oauth": ApplicationWizardAuthenticationByOauth;
    }
}
