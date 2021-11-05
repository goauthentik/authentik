import { LitElement, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Provider, ProvidersApi } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/EmptyState";
import "../../elements/PageHeader";
import "../../elements/buttons/SpinnerButton";
import "./ldap/LDAPProviderViewPage";
import "./oauth2/OAuth2ProviderViewPage";
import "./proxy/ProxyProviderViewPage";
import "./saml/SAMLProviderViewPage";

@customElement("ak-provider-view")
export class ProviderViewPage extends LitElement {
    @property({ type: Number })
    set providerID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG)
            .providersAllRetrieve({
                id: value,
            })
            .then((prov) => (this.provider = prov));
    }

    @property({ attribute: false })
    provider?: Provider;

    renderProvider(): TemplateResult {
        if (!this.provider) {
            return html`<ak-empty-state ?loading=${true} ?fullHeight=${true}></ak-empty-state>`;
        }
        switch (this.provider?.component) {
            case "ak-provider-saml-form":
                return html`<ak-provider-saml-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-saml-view>`;
            case "ak-provider-oauth2-form":
                return html`<ak-provider-oauth2-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-oauth2-view>`;
            case "ak-provider-proxy-form":
                return html`<ak-provider-proxy-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-proxy-view>`;
            case "ak-provider-ldap-form":
                return html`<ak-provider-ldap-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-ldap-view>`;
            default:
                return html`<p>Invalid provider type ${this.provider?.component}</p>`;
        }
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon="pf-icon pf-icon-integration"
                header=${ifDefined(this.provider?.name)}
                description=${ifDefined(this.provider?.verboseName)}
            >
            </ak-page-header>
            ${this.renderProvider()}`;
    }
}
