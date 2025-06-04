import "#admin/providers/google_workspace/GoogleWorkspaceProviderViewPage";
import "#admin/providers/ldap/LDAPProviderViewPage";
import "#admin/providers/microsoft_entra/MicrosoftEntraProviderViewPage";
import "#admin/providers/oauth2/OAuth2ProviderViewPage";
import "#admin/providers/proxy/ProxyProviderViewPage";
import "#admin/providers/rac/RACProviderViewPage";
import "#admin/providers/radius/RadiusProviderViewPage";
import "#admin/providers/saml/SAMLProviderViewPage";
import "#admin/providers/scim/SCIMProviderViewPage";
import "#admin/providers/ssf/SSFProviderViewPage";
import { DEFAULT_CONFIG } from "#common/api/config";
import "#components/ak-page-header";
import { AKElement } from "#elements/Base";
import "#elements/EmptyState";
import "#elements/buttons/SpinnerButton/ak-spinner-button";

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
            return html`<ak-empty-state loading ?fullHeight=${true}></ak-empty-state>`;
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
            case "ak-provider-rac-form":
                return html`<ak-provider-rac-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-rac-view>`;
            case "ak-provider-google-workspace-form":
                return html`<ak-provider-google-workspace-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-google-workspace-view>`;
            case "ak-provider-microsoft-entra-form":
                return html`<ak-provider-microsoft-entra-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-microsoft-entra-view>`;
            case "ak-provider-ssf-form":
                return html`<ak-provider-ssf-view
                    providerID=${ifDefined(this.provider.pk)}
                ></ak-provider-ssf-view>`;
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-view": ProviderViewPage;
    }
}
