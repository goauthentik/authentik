import "@goauthentik/admin/providers/ldap/LDAPProviderViewPage";
import "@goauthentik/admin/providers/oauth2/OAuth2ProviderViewPage";
import "@goauthentik/admin/providers/proxy/ProxyProviderViewPage";
import "@goauthentik/admin/providers/radius/RadiusProviderViewPage";
import "@goauthentik/admin/providers/saml/SAMLProviderViewPage";
import "@goauthentik/admin/providers/scim/SCIMProviderViewPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/buttons/SpinnerButton";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFPage from "@patternfly/patternfly/components/Page/page.css";

import { Provider, ProvidersApi } from "@goauthentik/api";

@customElement("ak-provider-view")
export class ProviderViewPage extends AKElement {
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

    static get styles(): CSSResult[] {
        return [PFPage];
    }

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
            case "ak-provider-scim-form":
                return html`<ak-provider-scim-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-scim-view>`;
            case "ak-provider-radius-form":
                return html`<ak-provider-radius-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-radius-view>`;
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
