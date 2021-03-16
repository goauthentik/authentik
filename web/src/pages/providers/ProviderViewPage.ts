import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/utils/LoadingState";

import "./SAMLProviderViewPage";
import "./OAuth2ProviderViewPage";
import "./ProxyProviderViewPage";
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
        return COMMON_STYLES.concat(css`
            * {
                height: 100%;
            }
        `);
    }

    render(): TemplateResult {
        if (!this.provider) {
            return html`<ak-loading-state></ak-loading-state>`;
        }
        switch (this.provider?.objectType) {
            case "saml":
                return html`<ak-provider-saml-view providerID=${ifDefined(this.provider.pk)}></ak-provider-saml-view>`;
            case "oauth2":
                return html`<ak-provider-oauth2-view providerID=${ifDefined(this.provider.pk)}></ak-provider-oauth2-view>`;
            case "proxy":
                return html`<ak-provider-proxy-view providerID=${ifDefined(this.provider.pk)}></ak-provider-proxy-view>`;
            default:
                return html`<p>Invalid provider type ${this.provider?.objectType}</p>`;
        }
    }
}
