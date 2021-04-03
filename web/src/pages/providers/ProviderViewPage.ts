import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";

import "../../elements/buttons/SpinnerButton";
import "../../elements/EmptyState";

import "./saml/SAMLProviderViewPage";
import "./oauth2/OAuth2ProviderViewPage";
import "./proxy/ProxyProviderViewPage";
import { Provider, ProvidersApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-provider-view")
export class ProviderViewPage extends LitElement {

    @property({type: Number})
    set providerID(value: number) {
        new ProvidersApi(DEFAULT_CONFIG).providersAllRead({
            id: value,
        }).then((prov) => (this.provider = prov));
    }

    @property({ attribute: false })
    provider?: Provider;

    static get styles(): CSSResult[] {
        return [css`
            * {
                height: 100%;
            }
        `];
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html`<ak-empty-state ?loading=${true} ?fullHeight=${true}></ak-empty-state>`;
        }
        switch (this.provider?.component) {
            case "ak-provider-saml-form":
                return html`<ak-provider-saml-view providerID=${ifDefined(this.provider.pk)}></ak-provider-saml-view>`;
            case "ak-provider-oauth2-form":
                return html`<ak-provider-oauth2-view providerID=${ifDefined(this.provider.pk)}></ak-provider-oauth2-view>`;
            case "ak-provider-proxy-form":
                return html`<ak-provider-proxy-view providerID=${ifDefined(this.provider.pk)}></ak-provider-proxy-view>`;
            default:
                return html`<p>Invalid provider type ${this.provider?.component}</p>`;
        }
    }
}
