import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import { renderForm } from "@goauthentik/admin/providers/oauth2/OAuth2ProviderFormForm.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { OAuth2ProviderRequest, SourcesApi } from "@goauthentik/api";
import { type OAuth2Provider, type PaginatedOAuthSourceList } from "@goauthentik/api";

import { ExtendedValidationError } from "../../types.js";
import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

@customElement("ak-application-wizard-provider-for-oauth")
export class ApplicationWizardOauth2ProviderForm extends ApplicationWizardProviderForm<OAuth2ProviderRequest> {
    label = msg("Configure OAuth2 Provider");

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

    renderForm(provider: OAuth2Provider, errors: ExtendedValidationError) {
        const showClientSecretCallback = (show: boolean) => {
            this.showClientSecret = show;
        };
        return html` <ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm(
                    provider ?? {},
                    errors,
                    this.showClientSecret,
                    showClientSecretCallback,
                )}
            </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("Oauth2 Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider as OAuth2Provider, this.wizard.errors);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-oauth": ApplicationWizardOauth2ProviderForm;
    }
}
