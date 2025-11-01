import "#admin/applications/wizard/ak-wizard-title";

import { ApplicationTransactionValidationError } from "../../types.js";
import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { renderForm } from "#admin/providers/oauth2/OAuth2ProviderFormForm";

import { OAuth2ProviderRequest, type PaginatedOAuthSourceList, SourcesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-application-wizard-provider-for-oauth")
export class ApplicationWizardOauth2ProviderForm extends ApplicationWizardProviderForm<OAuth2ProviderRequest> {
    label = msg("Configure OAuth2 Provider");

    @state()
    showClientSecret = true;

    @state()
    showLogoutMethod = false;

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

    renderForm(provider: OAuth2ProviderRequest, errors: ApplicationTransactionValidationError) {
        const showClientSecretCallback = (show: boolean) => {
            this.showClientSecret = show;
        };
        const showLogoutMethodCallback = (show: boolean) => {
            this.showLogoutMethod = show;
        };
        return html` <ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm({
                    provider,
                    errors,
                    showClientSecret: this.showClientSecret,
                    showClientSecretCallback,
                    showLogoutMethod: this.showLogoutMethod,
                    showLogoutMethodCallback,
                })}
            </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("Oauth2 Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider, this.wizard.errors);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-oauth": ApplicationWizardOauth2ProviderForm;
    }
}
