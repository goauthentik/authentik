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
import "#admin/providers/wsfed/WSFederationProviderViewPage";
import "#elements/EmptyState";
import "#elements/buttons/SpinnerButton/ak-spinner-button";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import { Provider, ProvidersApi } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";

import { css, CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFPage from "@patternfly/patternfly/components/Page/page.css";

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

    static styles: CSSResult[] = [
        PFPage,
        css`
            [part="content"] {
                display: flex;
                flex-flow: column;
                flex: 1 1 auto;
            }
        `,
    ];

    render(): TemplateResult {
        if (!this.provider) {
            return html`<ak-empty-state loading full-height></ak-empty-state>`;
        }

        const props = {
            providerID: this.provider.pk,
            part: "content",
        };

        switch (this.provider?.component) {
            case "ak-provider-saml-form":
                return html`<ak-provider-saml-view ${spread(props)}></ak-provider-saml-view>`;
            case "ak-provider-oauth2-form":
                return html`<ak-provider-oauth2-view ${spread(props)}></ak-provider-oauth2-view>`;
            case "ak-provider-proxy-form":
                return html`<ak-provider-proxy-view ${spread(props)}></ak-provider-proxy-view>`;
            case "ak-provider-ldap-form":
                return html`<ak-provider-ldap-view ${spread(props)}></ak-provider-ldap-view>`;
            case "ak-provider-scim-form":
                return html`<ak-provider-scim-view ${spread(props)}></ak-provider-scim-view>`;
            case "ak-provider-radius-form":
                return html`<ak-provider-radius-view ${spread(props)}></ak-provider-radius-view>`;
            case "ak-provider-rac-form":
                return html`<ak-provider-rac-view ${spread(props)}></ak-provider-rac-view>`;
            case "ak-provider-google-workspace-form":
                return html`<ak-provider-google-workspace-view
                    ${spread(props)}
                ></ak-provider-google-workspace-view>`;
            case "ak-provider-microsoft-entra-form":
                return html`<ak-provider-microsoft-entra-view
                    ${spread(props)}
                ></ak-provider-microsoft-entra-view>`;
            case "ak-provider-ssf-form":
                return html`<ak-provider-ssf-view ${spread(props)}></ak-provider-ssf-view>`;
            case "ak-provider-wsfed-form":
                return html`<ak-provider-wsfed-view ${spread(props)}></ak-provider-wsfed-view>`;
            default:
                return html`<p>Invalid provider type ${this.provider?.component}</p>`;
        }
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-integration",
            header: this.provider?.name,
            description: this.provider?.verboseName,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-view": ProviderViewPage;
    }
}
